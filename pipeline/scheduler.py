import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pipeline.tasks import process_task
from datetime import datetime

scheduler = BlockingScheduler()

def run_scraper():
    print(f"🚀 Scraper started at {datetime.now()}")
    process_task()
    print(f"✅ Scraper finished at {datetime.now()}")

# Jadwal scraping — setiap hari jam 08:00 pagi
scheduler.add_job(
    run_scraper,
    CronTrigger(hour=8, minute=0),
    # IntervalTrigger(minutes=2),
    id="daily_scrape",
    name="Daily Amazon Scraper",
    replace_existing=True,
)

if __name__ == "__main__":
    print("⏰ Scheduler started — scraper akan jalan tiap hari jam 08:00")
    print("   Tekan Ctrl+C untuk stop")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped.")
        scheduler.shutdown()