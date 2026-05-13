# ==========================================
# ★ 下記の " " の中に、ご自身のAPIキーを貼り付けてください
GROQ_API_KEY = "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"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile

# ページの基本設定
st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

st.title("🎙️ AI文字起こし＆翻訳・要約ツール (最新版)")
st.write("マイクをタップして話し、話し終わったら「停止（Done）」を押してください。")

# 言語選択
input_lang = st.radio(
    "🗣️ 話す言語を選択してください",
    ["自動検出 (Auto)", "日本語 (Japanese)", "英語 (English)"],
    horizontal=True
)

# 🌟 スマホでも安定して動く最新のマイク機能
audio_value = st.audio_input("🎤 ここをタップして録音開始")

if audio_value:
    # 埋め込んだキーを使用してGroqクライアントを準備
    client = Groq(api_key=GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ Groq AIが解析中..."):
        try:
            # 1. 音声から文字起こし
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
            
            # 2. AI（Llama 3.3）への詳細な指示
            prompt = f"""
            以下のテキストは、音声認識された会話の文字起こしです。
            内容を分析し、以下のフォーマットで出力してください。

            【元のテキスト】
            {recognized_text}

            【指示】
            ・文脈から判断して、複数の人物が話している場合は「A:」「B:」のように発言者を区別して台本形式にしてください。
            ・英語の場合は日本語訳を付け、最後に内容を箇条書きで要約してください。
            ・日本語の場合は、読みやすく整形した上で、最後に箇条書きで要約してください。

            【出力形式】
            ### 📝 内容の要約
            [ここに箇条書き]

            ### 🗣️ 文字起こし・翻訳結果
            [A: 〇〇〇]
            [B: 〇〇〇]
            """
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "あなたは優秀な同時通訳者・編集者です。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.choices[0].message.content
            
            # 3. 画面表示
            st.success("処理が完了しました！✨")
            st.markdown(result_text)
            
            # 🌟 4. ダウンロード機能
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
            # 一時ファイルを削除
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)