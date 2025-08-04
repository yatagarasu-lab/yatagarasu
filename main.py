from flask import Flask
from routes.dropbox_webhook import dropbox_bp
from routes.line_webhook import line_webhook_bp

app = Flask(__name__)

# Blueprint登録（URLルーティング）
app.register_blueprint(dropbox_bp)
app.register_blueprint(line_webhook_bp)

# 簡易ルート
@app.route("/")
def index():
    return "YATAGARASU Webhook Server is running!"

# Flaskアプリの起動（Renderで使われるため通常は必要なし）
if __name__ == "__main__":
    app.run(debug=True)