import asyncio
import sys
from datetime import datetime

from pipeline.tasks import process_task


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main():
    print(f"🚀 Scraper started at {datetime.now()}")

    scraped_count = asyncio.run(process_task())

    print(f"✅ Scraper finished at {datetime.now()}")
    print(f"📦 Products scraped: {scraped_count}")


if __name__ == "__main__":
    main()