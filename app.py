# ==========================================
# ★ ここにご自身のGroq APIキーを貼り付けます
GROQ_API_KEY = "gsk_ここにあなたの実際のAPIキーを貼り付けてください"
# ==========================================

import streamlit as st
from groq import Groq
import os
import tempfile

st.set_page_config(page_title="AI文字起こし＆要約ツール", layout="wide")

st.title("🎙️ AI文字起こし＆翻訳・要約ツール (完全スマホ対応版)")
st.write("マイクアイコンをタップして話し、話し終わったら停止ボタンを押してください。")

input_lang = st.radio(
    "🗣️ 話す言語を選択してください",
    ["自動検出 (Auto)", "日本語 (Japanese)", "英語 (English)"],
    horizontal=True
)

# 🌟 劇的改善：Streamlit公式の安定したマイク録音機能を使用！
audio_value = st.audio_input("🎤 ここをタップして録音開始")

if audio_value:
    client = Groq(api_key=GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        # 新しいマイク機能のデータを保存
        temp_audio.write(audio_value.getvalue())
        temp_audio_path = temp_audio.name

    with st.spinner("⚡ Groq AIが超高速で処理しています... 少々お待ちください"):
        try:
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
            
            # 🌟 追加：話者分離とフォーマットをAIに細かく指示する
            prompt = f"""
            以下のテキストは、音声認識された会話の文字起こしです。
            この内容を分析し、指定されたフォーマットで出力してください。

            【元のテキスト】
            {recognized_text}

            【指示】
            １．文脈や相槌などの会話の流れから発言者を推測し、複数の人物が話している場合は「A:」「B:」のように発言者ごとに改行して台本のようにしてください。（一人語りの場合は不要です）
            ２．テキストが「英語」の場合は、自然な日本語に翻訳し、その内容を箇条書きで要約してください。
            ３．テキストが「日本語」の場合は、そのまま内容を箇条書きで簡潔に要約し、必要であれば元の文章を読みやすく整形してください。

            【出力形式】
            ### 📝 要約
            [ここに箇条書きの要約]

            ### 🗣️ 発言者ごとの文字起こし（＆翻訳）
            [A: 〇〇〇]
            [B: 〇〇〇]
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
            
            # 結果を画面に表示
            st.markdown(result_text)
            
            # 🌟 追加：ダウンロード機能
            st.markdown("---") # 区切り線
            st.subheader("💾 結果の保存")
            
            export_text = f"【元の音声（生データ）】\n{recognized_text}\n\n【AIによる分析・翻訳結果】\n{result_text}"
            
            st.download_button(
                label="📥 この結果をテキストファイルでダウンロードする",
                data=export_text,
                file_name="ai_translation_result.txt",
                mime="text/plain"
            )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            os.remove(temp_audio_path)