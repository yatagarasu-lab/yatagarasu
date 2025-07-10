from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "仮デプロイ成功！（このあと本番コードに戻してOK）"

if __name__ == '__main__':
    app.run()