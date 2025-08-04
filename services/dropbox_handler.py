from flask import request, Response
from services.file_utils import list_dropbox_files, download_dropbox_file
from services.gpt_summarizer import summarize_content

def handle_dropbox_webhook(req):
    if req.method == 'GET':
        return Response(req.args.get('challenge'), mimetype='text/plain')
    
    print("🔔 Dropbox webhook triggered")

    try:
        file_paths = list_dropbox_files()
        for path in file_paths:
            content = download_dropbox_file(path)
            summary = summarize_content(content)
            print(f"📄 {path} → 要約: {summary[:100]}...")

        return Response("OK", status=200)
    except Exception as e:
        print(f"❌ Error: {e}")
        return Response("Internal Server Error", status=500)