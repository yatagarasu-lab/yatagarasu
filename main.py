import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from utils.analyze_file import analyze_file
from dropbox_utils import move_file_to_month_folder

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return 'LINE × Dropbox × GPTサーバー 起動中'

@app.route('/webhook', methods=['POST'])
def dropbox_webhook():
    if request.method == 'POST':
        # Dropbox webhookは確認用のGETと通知用のPOSTが来る
        if request.headers.get('X-Dropbox-Signature') is None:
            return '', 403

        try:
            # ここでは簡略化のためログだけ記録し、polling処理に任せる
            print('[Dropbox Webhook] ファイルが変更されました')
            return '', 200
        except Exception as e:
            print(f'[エラー] Dropbox webhook処理失敗: {e}')
            return '', 500

    return abort(400)

@app.route('/analyze', methods=['POST'])
def manual_analyze():
    data = request.get_json()
    dropbox_path = data.get('dropbox_path')

    if not dropbox_path:
        return {"error": "dropbox_pathが指定されていません"}, 400

    # 夜間のみ実行（22:00～翌6:00）
    from datetime import datetime
    now_hour = datetime.now().hour
    if not (now_hour >= 22 or now_hour < 6):
        return {"status": "現在は夜間時間帯ではないため、処理をスキップしました"}, 200

    try:
        analyze_file(dropbox_path)
        return {"status": "解析完了"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == '__main__':
    app.run(debug=False)