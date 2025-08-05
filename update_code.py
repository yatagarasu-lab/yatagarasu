# update_code.py（受信したコードをファイルに保存）

from flask import request, jsonify
import os

def handle_code_update():
    data = request.get_json()

    filename = data.get("filename")
    code = data.get("code")

    if not filename or not code:
        return jsonify({"status": "error", "message": "filenameとcodeが必要です"}), 400

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        return jsonify({"status": "success", "message": f"{filename} にコードを保存しました"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
