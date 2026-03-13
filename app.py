"""
Reddit Linen Digest Bot
-----------------------
Runs a built-in scheduler so a single `python app.py` keeps the process
alive and fires the digest every day at SEND_TIME (default 10:00 AM).

For hosting on Railway / Render / Fly.io:
  - Set all env vars in the platform's dashboard
  - Start command: python app.py
"""

import schedule
import time
import logging
from datetime import datetime

from config import MAX_POSTS, SEND_TIME
from storage import init_db, mark_sent
from collector import fetch_posts
from emailer import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run_digest():
    log.info("=== Starting daily linen digest ===")
    try:
        init_db()

        posts = fetch_posts()
        log.info(f"Fetched {len(posts)} relevant post(s) after filtering & dedup")

        top_posts = posts[:MAX_POSTS]
        send_email(top_posts)

        # Mark as sent ONLY after successful email
        for post in top_posts:
            mark_sent(post["post_id"], post["link"], post["title"])

        log.info(f"✅ Digest done — {len(top_posts)} post(s) sent, {len(posts) - len(top_posts)} extra filtered out")

    except Exception as e:
        log.error(f"❌ Digest failed: {e}", exc_info=True)


if __name__ == "__main__":
    log.info(f"🧵 Linen Digest Bot starting — will send daily at {SEND_TIME}")

    # Schedule the job
    schedule.every().day.at(SEND_TIME).do(run_digest)

    # Optionally fire immediately on first start so you can verify it works
    # (comment this out once confirmed working)
    log.info("Running once immediately for verification...")
    run_digest()

    # Keep alive — checks every 30 seconds
    while True:
        schedule.run_pending()
        time.sleep(30)
