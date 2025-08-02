from flask import Flask, request, jsonify
import requests
import json
import os
import io
import base64
from datetime import datetime, timedelta
from google.cloud import vision
from openai import OpenAI

app = Flask(__name__)

# === Google 認証JSONを環境変数から書き出し ===
def setup_google_credentials():
    b64 = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if b64:
        json_data = base64.b64decode(b64)
        cred_path = "/tmp/credentials.json"
        with open(cred_path, "wb") as f:
            f.write(json_data)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
        print("✅ Google 認証JSONロード完了")
    else:
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS_BASE64 が未設定")

setup_google_credentials()

# === Dropbox API（リフレッシュトークン方式） ===
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_access_token():
    try:
        url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN,
            "client_id": DROPBOX_CLIENT_ID,
            "client_secret": DROPBOX_CLIENT_SECRET
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✅ Dropbox アクセストークン取得成功")
        return token
    except Exception as e:
        print(f"❌ Dropbox アクセストークン取得失敗: {e}")
        return None

# === LINE API ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    try:
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "to": LINE_USER_ID,
            "messages": [{"type": "text", "text": message}]
        }
        res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
        res.raise_for_status()
        print("✅ LINE Push通知 成功")
    except Exception as e:
        print(f"❌ LINE通知失敗: {e}")

# === Webhook通知制限 ===
last_notification_time = None

# === Dropbox Webhook ===
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    global last_notification_time

    if request.method == "GET":
        challenge = request.args.get("challenge")
        print(f"✅ Dropbox webhook チャレンジ応答: {challenge}")
        return challenge, 200

    elif request.method == "POST":
        now = datetime.now()
        if last_notification_time and now - last_notification_time < timedelta(minutes=2):
            print("⏳ 通知スキップ（2分以内の連続）")
            return "", 200

        last_notification_time = now
        print("📦 Dropbox Webhook POST 受信 → 処理開始")
        process_latest_dropbox_image()
        return "", 200

# === LINE Webhook（返信テスト用） ===
@app.route("/line-webhook", methods=["POST"])
def line_webhook():
    payload = request.json
    try:
        events = payload.get("events", [])
        for event in events:
            if event.get("type") == "message" and event["message"].get("type") == "text":
                reply_token = event["replyToken"]
                reply_to_line(reply_token, "ありがとうございます")
        print("✅ LINE Webhook 正常受信")
    except Exception as e:
        print(f"❌ LINE Webhook エラー: {e}")
    return "OK", 200

def reply_to_line(reply_token, message):
    try:
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": message}]
        }
        requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=data)
        print("✅ LINE返信 成功")
    except Exception as e:
        print(f"❌ LINE返信失敗: {e}")

# === GPT + Google Cloud Vision API 統合 ===
def analyze_image_with_vision_and_gpt(image_bytes):
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)

        response = client.label_detection(image=image)
        labels = response.label_annotations
        label_texts = [label.description for label in labels]

        label_summary = ", ".join(label_texts)
        prompt = f"この画像には次のような要素が含まれています: {label_summary}。この内容を要約してください。"

        openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        gpt_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは画像の内容を要約するAIです。"},
                {"role": "user", "content": prompt}
            ]
        )
        summary = gpt_response.choices[0].message.content
        print("✅ GPT画像要約成功")
        return summary

    except Exception as e:
        print(f"❌ Vision+GPT解析失敗: {e}")
        return "解析失敗しました"

# === Google Vision API で文字検出（TEXT_DETECTION）===
def analyze_image_with_vision_api(image_content):
    try:
        api_key = os.getenv("GOOGLE_CLOUD_VISION_KEY")
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

        request_body = {
            "requests": [
                {
                    "image": {"content": base64.b64encode(image_content).decode("utf-8")},
                    "features": [{"type": "TEXT_DETECTION"}]
                }
            ]
        }

        res = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(request_body))
        res.raise_for_status()
        annotations = res.json()["responses"][0].get("textAnnotations", [])
        if annotations:
            detected_text = annotations[0]["description"]
            print("✅ Vision API テキスト解析成功")
            return detected_text
        else:
            print("⚠️ テキスト検出なし")
            return "テキストが検出されませんでした。"
    except Exception as e:
        print(f"❌ Vision APIエラー: {e}")
        return "画像解析に失敗しました。"

# === Dropboxから最新画像を取得 ===
def get_latest_dropbox_image():
    try:
        token = get_dropbox_access_token()
        if not token:
            return None, "Dropboxアクセストークン取得失敗"

        headers = {"Authorization": f"Bearer {token}"}
        list_res = requests.post(
            "https://api.dropboxapi.com/2/files/list_folder",
            headers=headers,
            json={"path": "/Apps/slot-data-analyzer", "recursive": False}
        )
        list_res.raise_for_status()
        entries = list_res.json().get("entries", [])
        image_entries = [f for f in entries if f[".tag"] == "file" and f["name"].lower().endswith((".jpg", ".jpeg", ".png"))]
        if not image_entries:
            return None, "画像ファイルが見つかりませんでした"

        latest = sorted(image_entries, key=lambda x: x["server_modified"], reverse=True)[0]
        path = latest["path_lower"]

        download_res = requests.post(
            "https://content.dropboxapi.com/2/files/download",
            headers={
                "Authorization": f"Bearer {token}",
                "Dropbox-API-Arg": json.dumps({"path": path})
            }
        )
        download_res.raise_for_status()
        return download_res.content, None
    except Exception as e:
        return None, f"Dropboxからの画像取得失敗: {e}"

# === Vision + GPT 処理メイン関数 ===
def process_latest_dropbox_image():
    image_data, err = get_latest_dropbox_image()
    if err:
        send_line_message(f"❌ 画像取得失敗: {err}")
        return

    summary = analyze_image_with_vision_and_gpt(image_data)
    send_line_message(f"📸 画像解析結果:\n\n{summary}")

# === テスト用：Vision単体で文字検出して通知 ===
@app.route("/run-vision-test", methods=["GET"])
def run_vision_test():
    image_data, err = get_latest_dropbox_image()
    if err:
        send_line_message(f"❌ Visionテスト失敗: {err}")
        return jsonify({"error": err}), 500

    text = analyze_image_with_vision_api(image_data)
    send_line_message(f"🧠 Vision解析結果:\n{text}")
    return jsonify({"text": text})

# === 動作チェック用ルート ===
@app.route("/", methods=["GET"])
def home():
    return "✅ AI統合サーバー稼働中"

# === Flask起動 ===
if __name__ == "__main__":
    app.run(debug=True)