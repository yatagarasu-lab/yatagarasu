# ✅ 重複を防ぎ、/dropbox_auto を1回だけ定義
@app.route("/dropbox_auto", methods=["POST"])
def dropbox_auto_summary():
    try:
        path = get_latest_dropbox_file()
        if not path:
            notify_line("❌ Dropboxフォルダにファイルが見つかりません。")
            return "no file", 200

        content = download_dropbox_file_content(path)
        if not content:
            notify_line("❌ Dropboxファイルの中身取得に失敗しました。")
            return "error", 500

        notify_line("📥 Dropboxの最新ファイルを取得しました。\n要約を開始します。")
        summary = gpt_summarize(content)

        # ファイル名を日付付きで生成
        today = datetime.now().strftime("%Y-%m-%d_%H-%M")
        github_filename = f"dropbox_summary_{today}.md"

        # GitHubにPush
        status, result = push_to_github(
            filename=github_filename,
            content=summary,
            commit_message="📄 Dropboxファイル要約を追加"
        )

        if status:
            notify_line(f"✅ GitHubに要約をPushしました：{github_filename}")
        else:
            notify_line(f"❌ GitHubへのPush失敗：{result}")

        return "ok", 200
    except Exception as e:
        print("❌ dropbox_auto_summary エラー:", e)
        notify_line(f"❌ Dropbox要約処理エラー:\n{e}")
        abort(500)