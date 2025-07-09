import os
from utils.ocr_utils import extract_text_from_image
from utils.gpt_utils import summarize_and_tag_text
from utils.line_utils import send_custom_line_notification
from utils.dropbox_utils import move_file_to_month_folder

# 環境変数からLINEユーザーIDを取得（Push通知宛先）
USER_ID = os.getenv("LINE_USER_ID")

def analyze_file(file_path):
    """
    Dropboxにアップされたファイルを解析し、要約とLINE通知を実行する。
    1. OCRで画像からテキスト抽出
    2. GPTで要約＋タグ生成
    3. Dropbox内でファイルを月別仕分けに移動
    4. LINEへ通知を送信
    """
    try:
        # 1. OCRでテキスト抽出
        extracted_text = extract_text_from_image(file_path)

        if not extracted_text.strip():
            extracted_text = "画像内から読み取れる文字がありませんでした。"

        # 2. GPTで要約とタグ付け
        summary = summarize_and_tag_text(extracted_text)

        # 3. Dropboxで月別フォルダへ移動
        new_path = move_file_to_month_folder(file_path)

        # 4. LINE通知送信
        send_custom_line_notification(USER_ID, summary, new_path)

        print(f"[OK] ファイル解析完了: {new_path}")

    except Exception as e:
        print(f"[ERROR] ファイル解析中にエラーが発生: {e}")