import openai
import os
import base64

# OpenAI APIキーを環境変数から取得
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# テキストメッセージをGPTで処理
def process_with_gpt(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはDropboxに保存されたスロット関連データを分析・要約するAIアシスタントです。"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPTエラー] {e}"

# 画像データをGPT Visionで処理
def process_with_gpt_image(image_binary, prompt="この画像を要約・分析してください。"):
    try:
        # 画像をbase64エンコード
        encoded_image = base64.b64encode(image_binary).decode('utf-8')

        # Vision APIに送信
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは画像の内容を分析・要約するAIアシスタントです。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                    ]
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPT画像エラー] {e}"