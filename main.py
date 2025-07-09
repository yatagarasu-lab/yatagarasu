from flask import Flask
from webhook import webhook_bp
from line_bot import line_bp
import os
from dotenv import load_dotenv
from log_utils import delete_old_logs  # ログ削除機能をインポート

load_dotenv()

# ▼ ログ削除（7日以上前の.logファイルを削除）
delete_old_logs(keep_days=7)

app = Flask(__name__)

# Blueprint登録
app.register_blueprint(webhook_bp)
app.register_blueprint(line_bp)

# Renderのヘルスチェック用
@app.route("/", methods=["GET"])
def index():
    return "LINE×Dropbox連携Bot：稼働中"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)