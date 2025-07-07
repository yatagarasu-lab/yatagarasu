def build_summary_message(summaries):
    message = "🧠 画像解析まとめ\n\n"
    for summary in summaries:
        message += summary + "\n\n"

    message += "📝 以上が今回の解析結果です。"
    return message
