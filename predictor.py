import os
import json
import datetime
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PREDICTION_FILE = "prediction_log.json"
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY)


def load_predictions():
    if os.path.exists(PREDICTION_FILE):
        with open(PREDICTION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_predictions(data):
    with open(PREDICTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_prediction_cycle(today_summary: str, result_summary: str = None) -> str:
    date_str = datetime.date.today().isoformat()
    data = load_predictions()

    # 前日の予測と結果の照合
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    feedback = ""
    if yesterday in data and "予測" in data[yesterday] and result_summary:
        prompt = f"""昨日（{yesterday}）のスロット予測と実際の結果を照合し、精度や傾向を評価してください。
        【予測内容】\n{data[yesterday]["予測"]}
        【実際の結果】\n{result_summary}
        今後に活かせる改善点や注目傾向もあれば述べてください。"""
        res = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "system", "content": "あなたはスロット設定傾向予測の専門家です。"},
                      {"role": "user", "content": prompt}]
        )
        feedback = res.choices[0].message.content.strip()
        data[yesterday]["答え合わせ"] = feedback

    # 本日の予測（新規生成）
    prompt_today = f"""以下の要約情報に基づき、明日のスロット店舗・台の設定投入傾向を予測してください。
    【前日までの結果分析】\n{feedback if feedback else 'なし'}
    【今日の収集データ要約】\n{today_summary}
    傾向、狙い目店舗、狙い機種、末尾など具体的に示してください。"""
    res = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "system", "content": "あなたはスロットの設定予測AIです。"},
                  {"role": "user", "content": prompt_today}]
    )
    prediction = res.choices[0].message.content.strip()

    data[date_str] = {
        "予測": prediction,
        "実績": result_summary or ""
    }

    save_predictions(data)
    return prediction
