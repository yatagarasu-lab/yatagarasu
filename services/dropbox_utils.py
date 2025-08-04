import dropbox

# Dropbox内のファイルをリストで取得（再帰的に）
def list_files(folder_path, dbx: dropbox.Dropbox):
    result = dbx.files_list_folder(folder_path, recursive=True)
    files = result.entries

    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)

    # ファイルのみ（FolderMetadataでないもの）を返す
    return [f for f in files if isinstance(f, dropbox.files.FileMetadata)]

# Dropboxからファイルをダウンロード（バイナリ形式）
def download_file(path, dbx: dropbox.Dropbox):
    metadata, res = dbx.files_download(path)
    return res.content
