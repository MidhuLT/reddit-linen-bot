from urllib.parse import quote_plus
import feedparser
from config import QUERIES, SUBREDDITS, LINEN_KEYWORDS
from storage import was_sent


# --------------------------------------------------------------------------- #
# URL builders
# --------------------------------------------------------------------------- #

def _global_rss(query: str) -> str:
    return f"https://www.reddit.com/search.rss?q={quote_plus(query)}&sort=new&t=week"

def _subreddit_rss(subreddit: str, query: str) -> str:
    return (
        f"https://www.reddit.com/r/{subreddit}/search.rss"
        f"?q={quote_plus(query)}&restrict_sr=1&sort=new&t=week"
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _extract_post_id(link: str) -> str:
    """Pull the Reddit post ID out of a permalink."""
    parts = link.strip("/").split("/")
    if "comments" in parts:
        idx = parts.index("comments")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return link

def _is_linen_related(title: str, summary: str) -> bool:
    """Return True only if the post clearly mentions linen."""
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in LINEN_KEYWORDS)

def _relevance_score(title: str, summary: str) -> int:
    """Higher score = more relevant. Used to sort the final list."""
    combined = (title + " " + summary).lower()
    score = 0
    # Reward each linen keyword match
    score += sum(combined.count(kw) for kw in LINEN_KEYWORDS)
    # Extra points if 'linen' is in the title itself (more on-topic)
    if "linen" in title.lower():
        score += 5
    return score

def _parse_feed(url: str, subreddit_label: str, query: str) -> list:
    """Fetch an RSS feed and return a list of raw post dicts."""
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[collector] Feed error ({url}): {e}")
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


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def fetch_posts() -> list:
    raw_posts = []

    # 1. Global Reddit search for each query
    for query in QUERIES:
        raw_posts.extend(_parse_feed(_global_rss(query), "global", query))

    # 2. Subreddit-specific searches
    for subreddit in SUBREDDITS:
        for query in QUERIES:
            raw_posts.extend(_parse_feed(_subreddit_rss(subreddit, query), subreddit, query))

    # 3. Filter, deduplicate, score
    seen     = set()
    filtered = []

    for post in raw_posts:
        if not post["link"]:
            continue

        # Must actually be about linen
        if not _is_linen_related(post["title"], post["summary"]):
            continue

        post_id = _extract_post_id(post["link"])

        # Skip duplicates within this run
        if post_id in seen:
            continue

        # Skip posts already emailed in a previous run
        if was_sent(post_id):
            continue

        seen.add(post_id)
        post["post_id"] = post_id
        post["score"]   = _relevance_score(post["title"], post["summary"])
        filtered.append(post)

    # 4. Sort by relevance score (most relevant first)
    filtered.sort(key=lambda p: p["score"], reverse=True)

    return filtered
