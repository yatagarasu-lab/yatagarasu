import openai
import os
from PIL import Image
import base64
from io import BytesIO

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_image(image_bytes):
    """
    画像バイトデータをGPT-4 Visionで解析して要約テキストを返す関数
    :param image_bytes: バイト型画像データ（Dropboxから取得した画像）
    :return: 要約または解析結果のテキスト
    """
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "この画像の内容を要約し、わかりやすく説明してください。"
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        result = response.choices[0].message["content"]
        return result

    except Exception as e:
        print(f"❌ GPT画像解析エラー: {e}")
        return f"⚠️ 画像の解析中にエラーが発生しました: {e}"