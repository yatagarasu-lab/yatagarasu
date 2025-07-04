import openai
import os
from PIL import Image
import io
import base64

openai.api_key = os.environ["OPENAI_API_KEY"]

def process_with_gpt(text):
    """テキスト内容をGPTで処理（解析 or 要約）"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "スロット設定情報を要約・分析してください。"},
                {"role": "user", "content": text}
            ]
        )
        result = response.choices[0].message.content
        print("🧠 GPT結果:", result)
        return result
    except Exception as e:
        print("⚠️ GPT処理エラー:", e)
        return None

def process_with_gpt_image(image_bytes):
    """画像内容をGPTで処理（OCR＋分析）"""
    try:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "この画像からスロット設定を推測・要約してください"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ],
            max_tokens=1000
        )
        result = response.choices[0].message.content
        print("🧠 GPT画像分析結果:", result)
        return result
    except Exception as e:
        print("⚠️ GPT画像処理エラー:", e)
        return None