# main.py（八咫烏本体）

import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# E.T Code の最新URL（必ずこのURLに更新）
ET_CODE_ENDPOINT = "https://e-t-code.onrender.com/receive"

@app.route("/", methods=["GET"])
def health_check():
    return "八咫烏 ONLINE"

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    # Dropbox Webhookからの通知
    payload = request.json
    print("📦 Webhook payload received:", json.dumps(payload, indent=2))

    # 通知データをそのまま E.T Code 側へ転送
    try:
        response = requests.post(ET_CODE_ENDPOINT, json=payload)
        response.raise_for_status()
        return jsonify({"status": "success", "forwarded_to_et_code": True})
    except requests.exceptions.RequestException as e:
        print("❌ Error forwarding to E.T Code:", e)
        return jsonify({"status": "error", "message": str(e)}), 500