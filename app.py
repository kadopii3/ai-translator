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

    with st.spinner("⚡ 大容量ファイルを最適化して解析中..."):
        chunk_paths = []
        try:
            chunk_paths = process_audio(temp_audio_path)
            full_transcript = ""
            progress_bar = st.progress(0)
            
            if not chunk_paths:
                st.error("音声データの解析に失敗しました。")
            else:
                for i, path in enumerate(chunk_paths):
                    with open(path, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-large-v3", file=f, response_format="json"
                        )
                        full_transcript += transcript.text + " "
                    progress_bar.progress(int(((i + 1) / len(chunk_paths)) * 100))

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"以下の内容を読みやすく整形し（必要ならA: B:と話者分離）、最後に箇条書きで要約してください:\n\n{full_transcript}"}]
                )
                
                result_text = response.choices[0].message.content
                st.success("全ての処理が完了しました！")
                st.markdown(f'<div class="result-box"><h3>🗣️ 解析結果</h3>{result_text}</div>', unsafe_allow_html=True)
                st.download_button("📥 この結果を保存", result_text, "ai_result.txt", use_container_width=True)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
            for p in chunk_paths:
                if os.path.exists(p): os.remove(p)
