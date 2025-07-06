import mimetypes
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    file_name = os.path.basename(file_path)

    if mime_type and mime_type.startswith("image/"):
        # 画像ファイルの場合 → ChatGPT Visionを使う
        with open(file_path, "rb") as image_file:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたはパチスロの設定判別を支援するAIです。画像内のスランプグラフや文字情報を読み取り、設定の傾向を分析してください。"},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_file.read().encode('base64').decode()}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
            )
        return response.choices[0].message.content.strip()

    else:
        # その他ファイル（例：PDF、テキスト）はプレーンテキストとして処理（必要なら後日対応）
        return f"{file_name} は画像ではありません。現在、画像のみ解析に対応しています。"