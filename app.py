# ==========================================
# ★ APIキーをご自身のものに書き換えてください
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile
from pydub import AudioSegment
import math

# ページの基本設定
st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

# カスタムCSS（UIデザインを維持）
st.markdown('''
    <style>
    .main-title {
        color: #0083B8; text-align: center; font-size: 3.2rem; font-weight: bold;
        margin-bottom: 0px; padding-bottom: 0px;
    }
    .sub-title {
        text-align: center; color: #555; font-size: 1.1rem;
        margin-top: 0px; margin-bottom: 20px;
    }
    /* 録音ボタンの装飾 */
    #root .stAudioInput button {
        width: 75px !important; height: 75px !important;
        border-radius: 50% !important; background-color: #28a745 !important;
        color: white !important; border: 4px solid #fff !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        margin: 0 auto !important; display: block !important;
    }
    #root .stAudioInput svg { width: 30px !important; height: 30px !important; }
    .result-box {
        background-color: #f8f9fa; border-radius: 10px; padding: 20px;
        border-left: 5px solid #0083B8; margin-top: 20px;
    }
    </style>
''', unsafe_allow_html=True)

# 音声分割関数 (25MB制限対策)
def process_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    # Groqの制限に合わせて1ファイルあたり約10分(or 20MB以下)を目安に分割
    chunk_length_ms = 10 * 60 * 1000 # 10分
    chunks = []
    
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        chunk.export(chunk_file.name, format="mp3")
        chunks.append(chunk_file.name)
    return chunks

st.markdown('<p class="main-title">🎙️ AI文字起こし＆要約ツール</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">長時間の会議は「ファイル保存」してからアップロードがおすすめです。</p>', unsafe_allow_html=True)

# 入力方法の選択
tab1, tab2 = st.tabs(["🎤 ブラウザで今すぐ録音", "📁 保存済みファイルを読み込む"])

audio_source = None

with tab1:
    input_lang = st.radio("🗣️ 言語", ["自動検出", "日本語", "英語"], horizontal=True, key="lang1")
    audio_source = st.audio_input("マイク")

with tab2:
    st.info("スマホのボイスメモやICレコーダーのファイルをここにドラッグしてください。")
    uploaded_file = st.file_uploader("音声ファイルを選択 (mp3, wav, m4a)", type=["mp3", "wav", "m4a"])
    if uploaded_file:
        audio_source = uploaded_file

# 共通処理
if audio_source:
    client = Groq(api_key=GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_source.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ 大容量ファイルを最適化して解析中..."):
        chunk_paths = []
        try:
            # 音声を解析して分割
            chunk_paths = process_audio(temp_audio_path)
            
            full_transcript = ""
            progress_bar = st.progress(0)
            
            for i, path in enumerate(chunk_paths):
                with open(path, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3", file=f, response_format="json"
                    )
                    full_transcript += transcript.text + " "
                progress_bar.progress(int(((i + 1) / len(chunk_paths)) * 100))

            # AIによる整形・要約
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"以下の内容を読みやすく整形し（必要ならA: B:と話者分離）、最後に箇条書きで要約してください:\n\n{full_transcript}"}]
            )
            
            result_text = response.choices[0].message.content
            st.success("全ての処理が完了しました！")
            st.markdown(f'<div class="result-box"><h3>🗣️ 解析結果</h3>{result_text}</div>', unsafe_allow_html=True)
            st.download_button("📥 この結果を保存", result_text, "ai_result.txt", use_container_width=True)
                
        except Exception as e:
            st.error(f"エラー: {e}")
        finally:
            if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
            for p in chunk_paths:
                if os.path.exists(p): os.remove(p)
