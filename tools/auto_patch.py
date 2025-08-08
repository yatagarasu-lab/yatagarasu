import os, subprocess, sys, datetime, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OPS = ROOT / "ops"
OPS.mkdir(exist_ok=True)

# 1) ハートビート（確実に差分を作る・安全）
stamp = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
(OPS / "last_run.log").write_text(f"autopatch heartbeat: {stamp}\n", encoding="utf-8")

# 2) main.py の先頭に非機能的バナーを埋め込む（壊さない）
main_py = ROOT / "main.py"
if main_py.exists():
    txt = main_py.read_text(encoding="utf-8", errors="ignore")
    start = "# === AUTO PATCH BANNER START ==="
    end   = "# === AUTO PATCH BANNER END ==="
    banner = f"{start}\n# Last auto-maintained: {stamp}\n{end}\n"
    if start in txt and end in txt:
        txt = re.sub(rf"{re.escape(start)}.*?{re.escape(end)}",
                     banner, txt, flags=re.S)
    else:
        # shebangやencodingの直後、from/importの前にだけ入れる
        lines = txt.splitlines(True)
        insert_at = 0
        for i, line in enumerate(lines[:20]):
            if line.lstrip().startswith(("from ", "import ")):
                insert_at = i
                break
        txt = "".join(lines[:insert_at]) + banner + "".join(lines[insert_at:])
    main_py.write_text(txt, encoding="utf-8")

# 3) （任意）OPENAI_API_KEY があれば将来ここで軽微な自動リファクタ等を実施
#    今は安全第一でノーオペ。壊さないのが正義。

# Git の差分がなければ終了
res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
if not res.stdout.strip():
    sys.exit(0)
# 差分はワークフロー側で commit/push