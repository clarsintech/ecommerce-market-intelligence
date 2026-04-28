import asyncio
import sys
from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler

from pipeline.tasks import process_task

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

scheduler = BlockingScheduler()

def run_scraper():
    print(f"🚀 Scraper started at {datetime.now()}")
    
    scraped_count = asyncio.run(process_task())
    
    print(f"✅ Scraper finished at {datetime.now()}")
    print(f"📦 Products scraped: {scraped_count}")

scheduler.add_job(
    run_scraper,
    CronTrigger(hour="0,12", minute=0, timezone="Asia/Jakarta"),
    id="amazon_price_scraper",
    name="Amazon Price Scraper",
    replace_existing=True,
)

if __name__ == "__main__":
    print("⏰ Scheduler started — scraper runs daily at 00:00 and 12:00 WIB")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped.")
        scheduler.shutdown()