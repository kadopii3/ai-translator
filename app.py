# ==========================================
# ★ 下記の " " の中に、ご自身のAPIキーを貼り付けてください
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile
import base64

# ページの基本設定
st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

# カスタムCSSで「丸いマイクボタン」の見た目を再現
st.markdown("""
    <style>
    .stAudioInput {
        max-width: 600px;
        margin: 0 auto;
    }
    /* タイトルの装飾 */
    .main-title {
        color: #0083B8;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🎙️ AI文字起こし＆翻訳・要約ツール</p>', unsafe_allow_html=True)
st.write("---")

# 言語選択（見た目をスッキリさせるためカラムを使用）
col1, col2 = st.columns([1, 2])
with col1:
    input_lang = st.radio(
        "🗣️ 話す言語",
        ["自動検出 (Auto)", "日本語 (Japanese)", "英語 (English)"],
        horizontal=True
    )

# 🎤 録音機能（公式の安定版。UIはCSSで調整されます）
audio_value = st.audio_input("ここをタップして録音開始")

if audio_value:
    # 直接書き込んだAPIキーを使用
    client = Groq(api_key=GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ AIが解析しています..."):
        try:
            # 1. 文字起こし
            lang_param = None
            if input_lang == "日本語 (Japanese)":
                lang_param = "ja"
            elif input_lang == "英語 (English)":
                lang_param = "en"

            with open(temp_audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-large-v3", 
                    file=audio_file,
                    language=lang_param,
                    response_format="json"
                )
            
            recognized_text = transcript.text
            
            # 2. AIによる分析（話者分離・要約）
            prompt = f"""
            以下のテキストを分析し、読みやすく整形してください。
            1. 複数人の会話なら「A:」「B:」と分けてください。
            2. 最後に箇条書きで要約を付けてください。
            
            テキスト:
            {recognized_text}
            """
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "あなたは優秀な編集者です。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.choices[0].message.content
            
            # 結果の表示
            st.success("処理が完了しました！")
            
            st.info("### 🗣️ 解析結果")
            st.markdown(result_text)
            
            # 🌟 ダウンロードボタンの表示
            st.write("---")
            st.subheader("💾 結果を保存する")
            
            export_data = f"【文字起こし】\n{recognized_text}\n\n【分析結果】\n{result_text}"
            
            # ダウンロードボタン
            st.download_button(
                label="📥 テキストファイルで保存",
                data=export_data,
                file_name="ai_summary.txt",
                mime="text/plain",
                use_container_width=True
            )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)