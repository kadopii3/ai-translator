# ==========================================
# ★ APIキーをご自身のものに書き換えてください
GROQ_API_KEY = "gsk_ここにあなたの実際のキーを貼り付け"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile

# ページの基本設定
st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

# カスタムCSSでデザインを大幅にカスタマイズ
st.markdown("""
    <style>
    /* 1. タイトルの大きさ（前回のまま大きく） */
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

    /* 2. 録音マイク（st.audio_input）を「丸い緑ボタン」にするCSS（サイズ調整版） */
    
    #root .stAudioInput {
        width: auto;
        max-width: 200px; /* 全体の幅を少し狭く */
        margin: 0 auto;   /* 中央寄せ */
        border: none;
        background: transparent;
    }

    /* 録音ボタン自体（緑色のまま、大きさを半分に：直径75px） */
    #root .stAudioInput button {
        width: 75px !important;   /* ★大きさを前回の半分に */
        height: 75px !important;  /* ★大きさを前回の半分に */
        border-radius: 50% !important; /* 完全に丸く */
        background-color: #28a745 !important; /* ★最初のバージョンのような緑色 */
        color: white !important;
        border: 4px solid #fff !important;   /* 白い枠線を少し細く */
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important; /* 影を少し控えめに */
        transition: all 0.3s ease;
        margin: 0 auto !important;
        display: block !important;
        padding: 0 !important; /* パディングをリセット */
    }

    /* ホバー時（マウスを乗せた時）の動き */
    #root .stAudioInput button:hover {
        background-color: #218838 !important; /* 少し濃い緑に */
        transform: scale(1.05); /* 少し大きく */
    }

    /* マイクアイコンの大きさと位置調整（ボタンに合わせて縮小） */
    #root .stAudioInput svg {
        width: 30px !important;  /* ★アイコンも小さく */
        height: 30px !important; /* ★アイコンも小さく */
        transform: translate(0px, 0px) !important;
    }

    /* 「ここをタップ」等のテキストを消す（アイコンだけにする） */
    #root .stAudioInput div[div="caption"] {
        display: none !important;
    }
    
    /* 録音中の時の赤い波紋アニメーション */
    #root .stAudioInput[data-testid="stAudioInputRecording"] button {
        background-color: #dc3545 !important; /* 録音中は赤に */
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(220, 53, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }

    /* 結果表示エリアの装飾 */
    .result-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #0083B8;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# タイトル表示
st.markdown('<p class="main-title">🎙️ AI文字起こし＆翻訳・要約ツール</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">マイクを押して話し、終わったらもう一度押してください。</p>', unsafe_allow_html=True)

# 言語選択
col1, col2, col3 = st.columns([1, 1.5, 1])
with col2:
    input_lang = st.radio("🗣️ 言語を選択", ["自動検出", "日本語", "英語"], horizontal=True)

st.write("") # スペース空け

# 🎤 ちょうどいい大きさの丸い緑色マイクボタン
audio_value = st.audio_input("マイク")

# 処理部分
if audio_value:
    client = Groq(api_key=GROQ_API_KEY)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ AIが解析中..."):
        try:
            with open(temp_audio_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-large-v3", file=f, response_format="json"
                )
            
            # AIによる整形
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"以下の内容を読みやすく整形（必要ならA: B:と話者分離）し、最後に箇条書きで要約してください:\n\n{transcript.text}"}]
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
            st.error(f"エラー: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
