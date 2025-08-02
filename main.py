from dropbox_client import upload_to_dropbox, read_from_dropbox

# ✅ 保存（GPTログや指示ファイルなど）
local_file = "gpt_log.txt"
dropbox_target_path = "/GPT記録/gpt_log.txt"
upload_to_dropbox(local_file, dropbox_target_path)

# ✅ 読み込み（指示書の読み込み）
remote_file = "/GPT記録/プロジェクト指示書.txt"
content = read_from_dropbox(remote_file)
print("📄 指示書の中身:\n", content)