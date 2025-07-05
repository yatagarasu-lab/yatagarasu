import zipfile
import io
import base64
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_zip_content(zip_data):
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            results = []

            for name in z.namelist():
                if name.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_bytes = z.read(name)
                    result = analyze_image(image_bytes, name)
                    results.append(f"🖼️ {name}:\n{result}")
                elif name.lower().endswith(".txt"):
                    text_data = z.read(name).decode("utf-8", errors="ignore")
                    result = analyze_text(text_data, name)
                    results.append(f"📄 {name}:\n{result}")
                else:
                    results.append(f"⛔ 未対応ファイル: {name}")

            return "\n\n".join(results)

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"

def analyze_image(image_bytes, name):
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはスロット台の設定をグラフ画像から予想するアナリストです。"},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                        {"type": "text", "text": f"この画像（{name}）から設定を予測してください。"}
                    ]
                },
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"画像解析エラー: {e}"

def analyze_text(text_data, name):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはスロットイベントの報告書から設定傾向を予測する専門家です。"},
                {"role": "user", "content": f"{name} の内容:\n{text_data}\n\nこの内容から得られる設定傾向を分析してください。"}
            ],
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"テキスト解析エラー: {e}"