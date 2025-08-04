import os
import json
import mimetypes

def is_text_file(filename):
    """
    拡張子ベースでテキストファイルかどうかを判定
    """
    text_extensions = ['.txt', '.md', '.csv', '.log', '.py', '.json']
    _, ext = os.path.splitext(filename.lower())
    return ext in text_extensions

def is_image_file(filename):
    """
    拡張子ベースで画像ファイルかどうかを判定
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    _, ext = os.path.splitext(filename.lower())
    return ext in image_extensions

def get_mime_type(filename):
    """
    MIMEタイプを推定（未設定なら application/octet-stream を返す）
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def decode_bytes(content):
    """
    バイナリからテキストへ安全に変換
    """
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return content.decode('shift_jis')
        except UnicodeDecodeError:
            return content.decode('latin1', errors='ignore')

def parse_json(content):
    """
    JSON文字列を辞書に変換（失敗時は None を返す）
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None