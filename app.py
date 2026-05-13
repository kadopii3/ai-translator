# ==========================================
# ★ APIキーをご自身のものに書き換えてください
GROQ_API_KEY = "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"
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
    /* 1. タイトルを2ポイント（約1.2倍）大きくし、色を調整 */
    .main-title {
        color: #0083B8;
        text-align: center;
        font-size: 3.2rem; /* 以前より大きく */
        font-weight: bold;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #555;
        font-size: 1.2rem;
        margin-top: 0px;
        margin-bottom: 30px;
    }

    /* 2. 録音マイク（st.audio_input）を「巨大な丸い緑ボタン」にする魔法のCSS */
    
    #root .stAudioInput {
        width: auto;
        max-width: 300px; /* 横幅を制限して丸く */
        margin: 0 auto;   /* 中央寄せ */
        border: none;
    }

    /* 録音ボタン自体（丸くして2倍の大きさに） */
    #root .stAudioInput button {
        width: 150px !important;  /* 巨大化（2倍くらい） */
        height: 150px !important; /* 巨大化（2倍くらい） */
        border-radius: 50% !important; /* 完全に丸く */
        background-color: #28a745 !important; /* ★最初のバージョンのような緑色 */
        color: white !important;
        border: 5px solid #fff !important;   /* 白い枠線 */
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important; /* 影をつけて立体的に */
        transition: all 0.3s ease;
        margin: 0 auto !important;
        display: block !important;
    }

    /* ホバー時（マウスを乗せた時）の動き */
    #root .stAudioInput button:hover {
        background-color: #218838 !important; /* 少し濃い緑に */
        transform: scale(1.05); /* 少し大きく */
    }

    /* マイクアイコンの大きさと位置調整 */
    #root .stAudioInput svg {
        width: 60px !important;
        height: 60px !important;
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
        70% { box-shadow: 0 0 0 20px rgba(220, 53, 69, 0); }
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

# タイトル表示（CSSで大きく装飾）
st.markdown('<p class="main-title">🎙️ AI文字起こし＆翻訳・要約ツール</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">下のマイクを押して話し、終わったらもう一度押してください。</p>', unsafe_allow_html=True)

# 言語選択
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    input_lang = st.radio("🗣️ 言語を選択", ["自動検出 (Auto)", "日本語", "英語"], horizontal=True)

st.write("") # スペース空け

# 🎤 巨大な緑色のマイクボタン（中身は st.audio_input で安定動作）
audio_value = st.audio_input("マイク")

# 処理部分
if audio_value:
    client = Groq(api_key=GROQ_API_KEY)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ AIが解析しています..."):
        try:
            with open(temp_audio_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-large-v3", file=f, response_format="json"
                )
            
            # 要約と話者分離の指示（より高品質に）
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"以下の内容を読みやすく整形（必要ならA: B:と話者分離）し、最後に箇条書きで要約してください:\n\n{transcript.text}"}]
            )
            
            result_text = response.choices[0].message.content
            
            st.success("処理が完了しました！")
            
            # 結果表示（カスタムCSS適用）
            st.markdown(f'<div class="result-box"><h3>🗣️ 解析結果</h3>{result_text}</div>', unsafe_allow_html=True)
            
            # ダウンロードボタン
            st.write("---")
            st.download_button(
                label="📥 この結果をテキストファイルで保存",
                data=result_text,
                file_name="ai_result.txt",
                mime="text/plain",
                use_container_width=True
            )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
