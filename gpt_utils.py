import openai
import base64
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")

def process_with_gpt(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはスロット分析AIです。"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPTエラー] {e}"

def process_with_gpt_image(image_binary, prompt="この画像を分析してください"):
    try:
        base64_image = base64.b64encode(image_binary).decode("utf-8")
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "あなたは画像分析AIです。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPT画像エラー] {e}"