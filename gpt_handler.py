import zipfile
import io
import hashlib
import openai

# OpenAI APIキーは環境変数で設定済みとする
openai.api_key = os.getenv("OPENAI_API_KEY")

def file_hash(content: bytes) -> str:
    """ファイルのハッシュを計算して重複チェック用に返す"""
    return hashlib.sha256(content).hexdigest()

def extract_files_from_zip(zip_data: bytes) -> dict:
    """ZIPファイルからファイルを抽出して辞書で返す"""
    extracted = {}
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
        for name in zip_file.namelist():
            if not name.endswith("/"):
                extracted[name] = zip_file.read(name)
    return extracted

def analyze_with_gpt(filename: str, content: bytes) -> str:
    """ファイルの中身をGPTで解析する"""
    try:
        if filename.endswith(('.txt', '.log')):
            text = content.decode('utf-8', errors='ignore')[:3000]
        else:
            text = f"ファイル {filename} は非テキスト形式のため内容省略。ファイルタイプ: {filename.split('.')[-1]}"
        
        prompt = f"以下の内容を要約または分析してください。\n\n{filename}:\n{text}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはデータ分析アシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"{filename} の解析中にエラー: {str(e)}"

def analyze_zip_content(zip_data: bytes) -> str:
    """ZIPの中身を一括でGPT解析してまとめて返す"""
    files = extract_files_from_zip(zip_data)
    seen_hashes = set()
    results = []

    for filename, content in files.items():
        content_hash = file_hash(content)
        if content_hash in seen_hashes:
            results.append(f"{filename}: ✅ 重複ファイルのためスキップ")
            continue

        seen_hashes.add(content_hash)
        result = analyze_with_gpt(filename, content)
        results.append(f"【{filename}】\n{result}\n")

    return "\n\n".join(results)