import streamlit as st
from groq import Groq
import os
import tempfile
import subprocess
import glob

# ==========================================
# ★ 金庫（Streamlit Secrets）からAPIキーを安全に呼び出す
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
# ==========================================

st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

st.markdown('''
    <style>
    .main-title { color: #0083B8; text-align: center; font-size: 3.2rem; font-weight: bold; margin-bottom: 0px; padding-bottom: 0px; }
    .sub-title { text-align: center; color: #555; font-size: 1.1rem; margin-top: 0px; margin-bottom: 20px; }
    div[data-testid="stAudioInput"] { max-width: 200px; margin: 0 auto !important; border: none !important; background: transparent !important; }
    div[data-testid="stAudioInput"] button {
        width: 75px !important; height: 75px !important; border-radius: 50% !important; background-color: #28a745 !important;
        color: white !important; border: 4px solid #fff !important; box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        margin: 0 auto !important; display: block !important;
    }
    div[data-testid="stAudioInput"] button:hover { background-color: #218838 !important; transform: scale(1.05); }
    div[data-testid="stAudioInput"] svg { width: 30px !important; height: 30px !important; }
    div[data-testid="stAudioInputRecording"] button { background-color: #dc3545 !important; }
    .result-box { background-color: #f8f9fa; border-radius: 10px; padding: 20px; border-left: 5px solid #0083B8; margin-top: 20px; }
    </style>
''', unsafe_allow_html=True)

def process_audio(file_path):
    temp_dir = tempfile.mkdtemp()
    output_pattern = os.path.join(temp_dir, "chunk_%03d.mp3")
    
    command = [
        "ffmpeg", "-y", "-i", file_path, 
        "-f", "segment", "-segment_time", "600", 
        "-ar", "16000", "-ac", "1", "-b:a", "32k", 
        output_pattern
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        chunks = sorted(glob.glob(os.path.join(temp_dir, "chunk_*.mp3")))
        return chunks
    except subprocess.CalledProcessError as e:
        raise Exception(f"音声処理エラー: {e.stderr.decode('utf-8', errors='ignore')}")

st.markdown('<p class="main-title">🎙️ AI文字起こし＆要約ツール</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">長時間の会議は「ファイル保存」してからアップロードがおすすめです。</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎤 ブラウザで今すぐ録音", "📁 保存済みファイルを読み込む"])

audio_source = None

with tab1:
    st.write("") 
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        input_lang = st.radio("🗣️ 言語を選択", ["自動検出", "日本語", "英語"], horizontal=True, key="lang1")
    audio_source = st.audio_input("マイク")

with tab2:
    st.info("スマホのボイスメモやICレコーダーのファイルをここにドラッグしてください。")
    uploaded_file = st.file_uploader("音声ファイルを選択 (mp3, wav, m4a)", type=["mp3", "wav", "m4a"])
    if uploaded_file:
        audio_source = uploaded_file

if audio_source:
    client = Groq(api_key=GROQ_API_KEY)
    
    original_ext = ".wav"
    if hasattr(audio_source, 'name'):
        _, original_ext = os.path.splitext(audio_source.name)
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as temp_audio:
        temp_audio.write(audio_source.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ 大容量ファイルを最適化して文字起こし中..."):
        chunk_paths = []
        try:
            chunk_paths = process_audio(temp_audio_path)
            raw_transcript = ""
            progress_bar = st.progress(0)
            
            if not chunk_paths:
                st.error("音声データの解析に失敗しました。")
            else:
                for i, path in enumerate(chunk_paths):
                    with open(path, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-large-v3", file=f, response_format="json"
                        )
                        raw_transcript += transcript.text + "\n"
                    progress_bar.progress(int(((i + 1) / len(chunk_paths)) * 100))

                st.info("📝 文字起こしが完了しました。続いて要約を作成しています...")

                # ★AIの「息切れ」を防ぐため、全文の書き直しをやめ、「要約の作成」に特化させます
                prompt = f"""
                以下の会議の文字起こし全文を読んで、主要な議題、重要な発言、決定事項などを分かりやすく箇条書きで要約してください。
                ※注意：文字起こしの全文を書き直す必要はありません。要約のみを出力してください。
                
                【文字起こし全文】
                """

                # 最新版から順番に試し、エラーが出たら次の安定版を自動で使う仕組み
                fallback_models = [
                    "llama3-8b-8192",    # Llama3の基本・安定版
                    "gemma2-9b-it",      # Googleが開発した安定モデル
                    "gemma-7b-it"        # 予備の予備
                ]
                summary_text = ""
                error_details = [] # エラーの本当の原因を記録するリスト
                
                for m_name in fallback_models:
                    try:
                        response = client.chat.completions.create(
                            model=m_name,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        summary_text = response.choices[0].message.content
                        break # 成功したらここで処理を完了する
                    except Exception as e:
                        error_details.append(f"【{m_name}】: {str(e)}")
                        continue # エラーになった場合は記録して次のモデルを試す
                
                if not summary_text:
                    error_msg = "\n".join(error_details)
                    raise Exception(f"全てのAIモデルが利用できませんでした。詳細な原因:\n{error_msg}")

                st.success("全ての処理が完了しました！")
                
                # 結果を分けて表示（要約はボックス内、全文は折りたたみ）
                st.markdown("### 📝 AI要約")
                st.markdown(f'<div class="result-box">{summary_text}</div>', unsafe_allow_html=True)
                
                st.markdown("### 🗣️ 文字起こし全文")
                with st.expander("クリックして全文を開く"):
                    st.write(raw_transcript)

                # ダウンロード内容も「要約＋全文」のセットにする
                export_data = f"【AI要約】\n{summary_text}\n\n================================\n\n【文字起こし全文】\n{raw_transcript}"
                
                st.download_button("📥 要約と全文を保存", export_data, "ai_result.txt", use_container_width=True)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
            for p in chunk_paths:
                if os.path.exists(p): os.remove(p)
