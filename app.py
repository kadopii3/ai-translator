# ==========================================
# ★ 下記の " " の中に、ご自身のAPIキーを貼り付けてください
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile

st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

st.title("🎙️ AI文字起こし＆翻訳・要約ツール (最新版)")
st.write("マイクをタップして話し、終わったら「停止（Done）」を押してください。")

input_lang = st.radio(
    "🗣️ 話す言語を選択してください",
    ["自動検出 (Auto)", "日本語 (Japanese)", "英語 (English)"],
    horizontal=True
)

audio_value = st.audio_input("🎤 ここをタップして録音開始")

if audio_value:
    # 🌟 ここが修正ポイントです！金庫(st.secrets)ではなく、上の変数を使います
    client = Groq(api_key=GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ AIが解析中..."):
        try:
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
            
            prompt = f"以下のテキストを分析し、A: B: のような話者分離、要約、翻訳を行ってください。\n\n{recognized_text}"
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "あなたは優秀な同時通訳者・編集者です。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.choices[0].message.content
            
            st.success("処理が完了しました！✨")
            st.markdown(result_text)
            
            st.markdown("---")
            st.subheader("💾 結果の保存")
            
            export_data = f"【元の文字起こし】\n{recognized_text}\n\n【分析結果】\n{result_text}"
            
            st.download_button(
                label="📥 この結果をテキストファイルでダウンロードする",
                data=export_data,
                file_name="transcription_result.txt",
                mime="text/plain"
            )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)