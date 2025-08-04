from apscheduler.schedulers.background import BackgroundScheduler
from yatagarasu import analyze_latest_file
import atexit

def start_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    
    # 5分おきに解析タスクを実行
    scheduler.add_job(analyze_latest_file, 'interval', minutes=5)
    
    scheduler.start()
    print("🕒 自動解析スケジューラ起動中（5分間隔）")

    # アプリ終了時にスケジューラも停止
    atexit.register(lambda: scheduler.shutdown())