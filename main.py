# === AUTO PATCH BANNER START ===
# Last auto-maintained: 2025-08-23T14:17:05Z
# === AUTO PATCH BANNER END ===
















































































































































































from flask import Flask, request, Response
import os, requests, hashlib, logging, json
import dropbox
from threading import Thread
from datetime import datetime, timezone
from tzlocal import get_localzone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage

# ============ 環境変数 ============
SERVICE_NAME = os.getenv("SERVICE_NAME", "SERVICE")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY       = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET    = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")
LINE_TOKEN            = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID          = os.getenv("LINE_USER_ID")
PARTNER_UPDATE_URL    = os.getenv("PARTNER_UPDATE_URL")
NOTIFY_SUMMARY        = os.getenv("NOTIFY_SUMMARY", "0") == "1"
NOTIFY_ERRORS         = os.getenv("NOTIFY_ERRORS", "1") == "1"
SCAN_INTERVAL_MIN     = int(os.getenv("SCAN_INTERVAL_MIN", "10"))
LOG_LEVEL             = os.getenv("LOG_LEVEL", "INFO").upper()

# ============ ログ ============
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(SERVICE_NAME)

# ============ 初期化 ============
app = Flask(__name__)

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

oai = OpenAI(api_key=OPENAI_API_KEY)
line = LineBotApi(LINE_TOKEN)

DROPBOX_FOLDER_PATH = ""  # ルート監視
PROCESSED_HASHES = set()
TZ = get_localzone()

# ============ メトリクス ============
FILES_SCANNED   = Counter("files_scanned_total", "Scanned files", ["service"])
FILES_NEW       = Counter("files_new_total", "New files processed", ["service"])
ERRORS_TOTAL    = Counter("errors_total", "Errors", ["service", "kind"])
LAST_SCAN_EPOCH = Gauge("last_scan_epoch_seconds", "Last scan timestamp", ["service"])

# ============ 通知 ============
def notify_line(text: str):
    try:
        line.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        log.warning("LINE通知失敗: %s", e)

def notify_error(kind: str, err: Exception):
    ERRORS_TOTAL.labels(service=SERVICE_NAME, kind=kind).inc()
    log.error("[%s] %s", kind, err)
    if NOTIFY_ERRORS:
        try:
            notify_line(f"【{SERVICE_NAME} エラー】{kind}\n{err}")
        except Exception:
            pass

# ============ Dropbox / OpenAI リトライ ============
retry_policy = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(Exception)
)

@retry(**retry_policy)
def list_files_page(folder: str, cursor: str = None):
    if cursor:
        return dbx.files_list_folder_continue(cursor)
    return dbx.files_list_folder(folder)

def list_files(folder_path=DROPBOX_FOLDER_PATH):
    entries = []
    try:
        folder = "" if folder_path in ("", "/") else folder_path
        res = list_files_page(folder)
        entries.extend(res.entries)
        while res.has_more:
            res = list_files_page(folder, res.cursor)
            entries.extend(res.entries)
    except Exception as e:
        notify_error("list_files", e)
    return entries

@retry(**retry_policy)
def download_file(path):
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        notify_error("download_file", e)
        return None

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content or b"").hexdigest()

@retry(**retry_policy)
def summarize_text(text: str) -> str:
    try:
        resp = oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "以下のテキストを日本語で簡潔に要約してください。"},
                {"role": "user", "content": text}
            ],
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        notify_error("summarize_text", e)
        return f"[要約失敗] {e}"

# ============ コア処理 ============
def process_new_files():
    start = datetime.now(TZ)
    files = list_files()
    LAST_SCAN_EPOCH.labels(service=SERVICE_NAME).set(datetime.now(timezone.utc).timestamp())

    for entry in files:
        fname = entry.name
        FILES_SCANNED.labels(service=SERVICE_NAME).inc()
        path = f"/{fname}" if DROPBOX_FOLDER_PATH in ("", "/") else f"{DROPBOX_FOLDER_PATH.rstrip('/')}/{fname}"

        content = download_file(path)
        if not content:
            continue

        h = file_hash(content)
        if h in PROCESSED_HASHES:
            continue
        PROCESSED_HASHES.add(h)
        FILES_NEW.labels(service=SERVICE_NAME).inc()

        text = content.decode("utf-8", errors="ignore")
        summary = summarize_text(text)

        if NOTIFY_SUMMARY:
            notify_line(f"【{SERVICE_NAME} 要約】{fname}\n{summary}")
        else:
            log.info("[要約] %s -> %s", fname, summary[:120].replace("\n"," "))

    log.info("Scan finished (%s) files=%d new=%d",
             start.strftime("%Y-%m-%d %H:%M:%S"),
             len(files),
             len(PROCESSED_HASHES))

def _handle_async():
    try:
        process_new_files()
        if PARTNER_UPDATE_URL:
            try:
                requests.post(PARTNER_UPDATE_URL, timeout=3)
            except Exception as e:
                notify_error("partner_update", e)
    except Exception as e:
        notify_error("async", e)

# ============ HTTP ============
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            return challenge, 200
        return "No challenge", 400

    Thread(target=_handle_async, daemon=True).start()
    return "", 200

@app.route("/update-code", methods=["POST"])
def update_code():
    Thread(target=_handle_async, daemon=True).start()
    return "OK", 200

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/healthz")
def healthz():
    try:
        # 軽い健診：ルート一覧1回
        _ = list_files()[:1]
        payload = {
            "service": SERVICE_NAME,
            "status": "ok",
            "hashes": len(PROCESSED_HASHES),
            "time": datetime.now(TZ).isoformat()
        }
        return Response(json.dumps(payload), mimetype="application/json", status=200)
    except Exception as e:
        notify_error("healthz", e)
        return "ng", 500

@app.route("/")
def home():
    files = list_files()
    names = "<br>".join([f.name for f in files])
    return f"<h2>{SERVICE_NAME} BOT 起動中</h2><p>{names}</p>"

# ============ スケジューラ ============
scheduler = BackgroundScheduler(timezone=str(TZ))
scheduler.add_job(process_new_files, "interval", minutes=SCAN_INTERVAL_MIN, id="scan_job", max_instances=1, coalesce=True)
scheduler.start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)