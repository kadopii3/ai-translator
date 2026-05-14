# ==========================================
# ★ APIキーをご自身のものに書き換えてください
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile
import wave
import math

# ページの基本設定
st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

# カスタムCSS（前回のUIデザインをそのまま維持）
st.markdown("""
    <style>
    .main-title {
        color: #0083B8;
        text-align: center;
        font-size: 3.2rem;
        font-weight: bold;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #555;
        font-size: 1.1rem;
        margin-top: 0px;
        margin-bottom: 20px;
    }
    #root .stAudioInput {
        width: auto;
        max-width: 200px; 
        margin: 0 auto;   
        border: none;
        background: transparent;
    }
    #root .stAudioInput button {
        width: 75px !important;   
        height: 75px !important;  
        border-radius: 50% !important; 
        background-color: #28a745 !important; 
        color: white !important;
        border: 4px solid #fff !important;   
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important; 
        transition: all 0.3s ease;
        margin: 0 auto !important;
        display: block !important;
        padding: 0 !important; 
    }
    #root .stAudioInput button:hover {
        background-color: #218838 !important; 
        transform: scale(1.05); 
    }
    #root .stAudioInput svg {
        width: 30px !important;  
        height: 30px !important; 
        transform: translate(0px, 0px) !important;
    }
    #root .stAudioInput div[div="caption"] {
        display: none !important;
    }
    #root .stAudioInput[data-testid="stAudioInputRecording"] button {
        background-color: #dc3545 !important; 
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(220, 53, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }
    .result-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #0083B8;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 音声ファイルを細かく分割する関数（25MB制限突破用）
def split_audio(file_path, chunk_length_sec=60):
    chunks = []
    try:
        with wave.open(file_path, 'rb') as wav:
            n_frames = wav.getnframes()
            frame_rate = wav.getframerate()
            frames_per_chunk = int(chunk_length_sec * frame_rate)
            n_chunks = math.ceil(n_frames / frames_per_chunk)

            for i in range(n_chunks):
                chunk_path = f"{file_path}_chunk{i}.wav"
                with wave.open(chunk_path, 'wb') as chunk_wav:
                    chunk_wav.setparams(wav.getparams())
                    wav.setpos(i * frames_per_chunk)
                    chunk_data = wav.readframes(frames_per_chunk)
                    chunk_wav.writeframes(chunk_data)
                chunks.append(chunk_path)
    except Exception as e:
        st.error(f"音声の分割中にエラーが発生しました: {e}")
    return chunks

# UI部分
st.markdown('<p class="main-title">🎙️ AI文字起こし＆翻訳・要約ツール</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">マイクを押して話し、終わったらもう一度押してください。</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1.5, 1])
with col2:
    input_lang = st.radio("🗣️ 言語を選択", ["自動検出", "日本語", "英語"], horizontal=True)

st.write("")

# マイク入力
audio_value = st.audio_input("マイク")

if audio_value:
    client = Groq(api_key=GROQ_API_KEY)
    
    # 1. 録音データを一時保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ 音声を分析・処理中...（長時間の録音は少し時間がかかります）"):
        chunk_paths = []
        try:
            # 2. 音声を60秒ごとに自動分割
            chunk_paths = split_audio(temp_audio_path, chunk_length_sec=60)
            
            full_transcript = ""
            
            # 3. 分割したファイルを順番にAIに投げて合体させる
            progress_bar = st.progress(0)
            st.info(f"音声を {len(chunk_paths)} 個のブロックに分けて処理しています...")
            
            for i, chunk_path in enumerate(chunk_paths):
                with open(chunk_path, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3", 
                        file=f, 
                        response_format="json"
                    )
                    full_transcript += transcript.text + "\n"
                
                # 進捗バーを更新
                progress = int(((i + 1) / len(chunk_paths)) * 100)
                progress_bar.progress(progress)

            # 4. 全てのテキストが揃ったら、Llamaで要約・整形
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"以下の内容を読みやすく整形（必要ならA: B:と話者分離）し、最後に箇条書きで要約してください:\n\n{full_transcript}"}]
            )
            
            result_text = response.choices[0].message.content
            
            st.success("完了！")
            
            # 結果表示
            st.markdown(f'<div class="result-box"><h3>🗣️ 解析結果</h3>{result_text}</div>', unsafe_allow_html=True)
            
            # ダウンロードボタン
            st.write("---")
            st.download_button(
                label="📥 この結果を保存",
                data=result_text,
                file_name="ai_result.txt",
                mime="text/plain",
                use_container_width=True
            )
                
        except Exception as e:
            st.error(f"処理エラー: {e}")
        finally:
            # 使い終わった一時ファイルを全て綺麗に削除（お掃除）
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            for chunk_path in chunk_paths:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
