# ==========================================
# ★ ここにご自身のGroq APIキーを貼り付けます
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from audio_recorder_streamlit import audio_recorder
from groq import Groq
import os
import tempfile

st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

st.title("🎙️ AI文字起こし＆翻訳・要約ツール (多言語・スマホ対応版)")
st.write("マイクアイコンをクリックして話し、もう一度クリックして停止してください。")

# 🌟 追加：言語選択オプション
input_lang = st.radio(
    "🗣️ 話す言語を選択してください",
    ["自動検出 (Auto)", "日本語 (Japanese)", "英語 (English)"],
    horizontal=True
)

audio_bytes = audio_recorder(
    text="クリックして録音開始 / 停止", 
    recording_color="#e81416", 
    neutral_color="#6aa84f",
    pause_threshold=600.0  # ← これを追加！無音が何秒続いたら自動ストップするか（600秒＝10分）
)

if audio_bytes:
    client = Groq(api_key=GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    st.audio(audio_bytes, format="audio/wav")
    
    with st.spinner("⚡ Groq AIが超高速で処理しています... 少々お待ちください"):
        try:
            # 🌟 追加：選択された言語をWhisper APIに伝える
            lang_param = None
            if input_lang == "日本語 (Japanese)":
                lang_param = "ja"
            elif input_lang == "英語 (English)":
                lang_param = "en"

            with open(temp_audio_path, "rb") as audio_file:
                if lang_param:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3", 
                        file=audio_file,
                        language=lang_param,
                        response_format="json"
                    )
                else:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-large-v3", 
                        file=audio_file,
                        response_format="json"
                    )
            
            recognized_text = transcript.text
            
            # 🌟 追加：言語に応じた賢いプロンプト（指示書）
            prompt = f"""
            以下のテキストを分析し、指定されたフォーマットで出力してください。

            【元のテキスト】
            {recognized_text}

            【指示】
            ・テキストが「英語」の場合は、自然な日本語に翻訳し、その内容を箇条書きで要約してください。
            ・テキストが「日本語」の場合は、そのまま内容を箇条書きで簡潔に要約し、必要であれば元の文章を読みやすく整形してください。

            【出力形式】
            ### 📝 要約
            [ここに箇条書きの要約]

            ### 🇯🇵 日本語訳（または読みやすい整形テキスト）
            [ここに結果]
            """
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "あなたは優秀な同時通訳者および編集者です。自然でわかりやすい日本語で出力してください。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.choices[0].message.content
            
            st.success("処理が完了しました！✨")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🗣️ 元の音声 (文字起こし)")
                st.info(recognized_text)
            
            with col2:
                st.markdown(result_text)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            os.remove(temp_audio_path)