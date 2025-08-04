from services.dropbox_handler import get_latest_dropbox_file_path
from yatagarasu import analyze_file
from line_notify import send_line_message

def test_dropbox_to_line_flow():
    print("STEP 1: Dropboxから最新ファイル取得中...")
    latest_path = get_latest_dropbox_file_path()
    if not latest_path:
        print("Dropboxに有効なファイルがありません。")
        return

    print(f"STEP 2: ファイルパス取得成功 → {latest_path}")
    
    print("STEP 3: ファイル解析中...")
    result = analyze_file(latest_path)
    print("STEP 4: 解析結果 →", result)

    print("STEP 5: LINE通知送信中...")
    send_line_message(f"解析結果：\n{result}")
    print("STEP 6: LINE通知送信完了！")

if __name__ == "__main__":
    test_dropbox_to_line_flow()
