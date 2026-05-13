# ==========================================
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile

st.set_page_config(page_title="AI文字起こしツール", layout="wide")

st.markdown('<p style="color:#0083B8; text-align:center; font-size:2rem; font-weight:bold;">🎙️ AI文字起こし＆要約ツール</p>', unsafe_allow_html=True)

# 言語選択
input_lang = st.radio("🗣️ 言語", ["自動検出 (Auto)", "日本語", "英語"], horizontal=True)

# 最新の安定した録音機能（クラウドではこれが一番確実です）
audio_value = st.audio_input("🎤 ここをタップして録音開始")

if audio_value:
    client = Groq(api_key=GROQ_API_KEY)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("AIが解析しています..."):
        try:
            with open(temp_audio_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-large-v3", file=f, response_format="json"
                )
            
            # 要約と話者分離の指示
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"以下の内容を話者分離し、要約してください:\n{transcript.text}"}]
            )
            
            st.success("完了しました！")
            st.markdown(response.choices[0].message.content)
            
            # 🌟 ダウンロードボタン
            st.download_button("📥 結果をテキストで保存", response.choices[0].message.content, "result.txt")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
