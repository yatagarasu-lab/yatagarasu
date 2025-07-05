import zipfile
import io
import base64
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def analyze_zip_content(zip_bytes: bytes) -> str:
    """
    ZIPファイルの内容を読み取り、画像やテキストをChatGPTで要約
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
            extracted_texts = []

            for name in zip_file.namelist():
                with zip_file.open(name) as file:
                    if name.endswith((".txt", ".csv")):
                        text_data = file.read().decode("utf-8", errors="ignore")
                        extracted_texts.append(f"【{name}】\n{text_data}\n")
                    elif name.endswith((".png", ".jpg", ".jpeg")):
                        image_bytes = file.read()
                        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                        image_prompt = {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"次の画像を解析して内容を要約してください（ファイル名: {name}）:"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                            ]
                        }
                        image_result = openai.chat.completions.create(
                            model="gpt-4-vision-preview",
                            messages=[image_prompt],
                            max_tokens=1000
                        )
                        extracted_texts.append(f"【{name}（画像）】\n{image_result.choices[0].message.content}\n")

            all_text = "\n\n".join(extracted_texts)

            # 全体要約
            final_summary = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはDropboxのZIPデータを要約・分析するAIです。"},
                    {"role": "user", "content": f"次のデータを要約・解析してください:\n{all_text}"}
                ],
                max_tokens=1500
            )

            return final_summary.choices[0].message.content

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"