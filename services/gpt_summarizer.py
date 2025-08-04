import os
import openai

# OpenAIのAPIキーを環境変数から取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# GPTを使ってテキストを要約する関数
def summarize_text(content, filename=None):
    try:
        # プロンプトの作成
        prompt = f"""
次のテキストはDropboxに保存されたファイルの内容です。
この内容を読み取り、以下の観点で要約・分析してください：

1. ファイルの種類（画像/スロット/メモ/実戦データなど）  
2. 重要なキーワード・設定差がある情報  
3. スロットの設定予測が可能ならその要因  
4. 全体の要点を3行以内にまとめる

--- ファイル内容（{filename or '無名ファイル'}） ---
{content[:4000]}  # 4000文字を上限に送信
"""

        # ChatGPT API呼び出し
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはDropboxから取得したスロット関連のファイルを自動要約・解析するアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ GPT要約エラー: {e}")
        return f"【GPTエラー】{e}"