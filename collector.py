from urllib.parse import quote_plus
import feedparser
import logging
import time
import random
from config import QUERIES, SUBREDDITS, LINEN_KEYWORDS
from storage import was_sent

log = logging.getLogger(__name__)

# Reddit blocks default feedparser user-agent on hosted servers.
# Using a browser-like User-Agent fixes this.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# --------------------------------------------------------------------------- #
# URL builders
# --------------------------------------------------------------------------- #

def _global_rss(query: str, window: str) -> str:
    return f"https://www.reddit.com/search.rss?q={quote_plus(query)}&sort=new&t={window}"

def _subreddit_rss(subreddit: str, query: str, window: str) -> str:
    return (
        f"https://www.reddit.com/r/{subreddit}/search.rss"
        f"?q={quote_plus(query)}&restrict_sr=1&sort=new&t={window}"
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _extract_post_id(link: str) -> str:
    parts = link.strip("/").split("/")
    if "comments" in parts:
        idx = parts.index("comments")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return link

def _is_linen_related(title: str, summary: str) -> bool:
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in LINEN_KEYWORDS)

def _relevance_score(title: str, summary: str) -> int:
    combined = (title + " " + summary).lower()
    score = sum(combined.count(kw) for kw in LINEN_KEYWORDS)
    if "linen" in title.lower():
        score += 5
    return score

def _parse_feed(url: str, subreddit_label: str, query: str) -> list:
    try:
        # Set browser-like User-Agent to avoid Reddit blocking hosted IPs
        feedparser.USER_AGENT = HEADERS["User-Agent"]
        feed = feedparser.parse(url, request_headers=HEADERS)

        if feed.bozo and feed.bozo_exception:
            log.debug(f"Feed note ({subreddit_label} / {query}): {feed.bozo_exception}")

        if not feed.entries:
            log.debug(f"No entries for: {url}")

    except Exception as e:
        log.warning(f"Feed error ({url}): {e}")
        return []

    results = []
    for entry in feed.entries:
        results.append({
            "title":     entry.get("title", ""),
            "link":      entry.get("link", ""),
            "summary":   entry.get("summary", ""),
            "published": entry.get("published", ""),
            "subreddit": subreddit_label,
            "query":     query,
        })
    return results


def _fetch_raw(window: str) -> list:
    """Fetch all raw posts with a small delay between requests to avoid rate limiting."""
    raw = []

    for query in QUERIES:
        raw.extend(_parse_feed(_global_rss(query, window), "global", query))
        time.sleep(random.uniform(1.0, 2.0))  # polite delay

    for subreddit in SUBREDDITS:
        for query in QUERIES:
            raw.extend(_parse_feed(_subreddit_rss(subreddit, query, window), subreddit, query))
            time.sleep(random.uniform(1.0, 2.0))  # polite delay

    log.info(f"Raw posts fetched (window={window}): {len(raw)}")
    return raw


def _filter_and_score(raw_posts: list) -> list:
    seen     = set()
    filtered = []

    for post in raw_posts:
        if not post["link"]:
            continue
        if not _is_linen_related(post["title"], post["summary"]):
            continue

        post_id = _extract_post_id(post["link"])

        if post_id in seen:
            continue
        if was_sent(post_id):
            continue

        seen.add(post_id)
        post["post_id"] = post_id
        post["score"]   = _relevance_score(post["title"], post["summary"])
        filtered.append(post)

    filtered.sort(key=lambda p: p["score"], reverse=True)
    return filtered


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def fetch_posts() -> list:
    """
    Smart rolling fetch logic:
    1. Try last 7 days first.
    2. If no new unseen posts, keep retrying with 30-day window up to 20 times.
    3. After 20 failed attempts, return empty list for 'no posts' email.
    """
    MAX_ITERATIONS = 20

    # --- Step 1: Try last 7 days ---
    log.info("Checking last 7 days for new linen posts...")
    posts = _filter_and_score(_fetch_raw("week"))

    if posts:
        log.info(f"✅ Found {len(posts)} new post(s) in last 7 days.")
        return posts

    log.info("No new posts in last 7 days. Starting rolling 30-day fallback...")

    # --- Step 2: Roll through 30-day window up to 20 times ---
    for iteration in range(1, MAX_ITERATIONS + 1):
        log.info(f"Attempt {iteration}/{MAX_ITERATIONS} — checking 30-day window...")
        posts = _filter_and_score(_fetch_raw("month"))

        if posts:
            log.info(f"✅ Found {len(posts)} new post(s) on attempt {iteration}.")
            return posts

        log.info(f"No new posts on attempt {iteration}.")

    # --- Step 3: Exhausted all attempts ---
    log.warning(f"❌ No new posts found after {MAX_ITERATIONS} attempts.")
    return []
