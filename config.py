import os
from dotenv import load_dotenv

load_dotenv()

TOPIC = os.getenv("TOPIC", "linen clothing")

# Search queries — keep them short and punchy for Reddit RSS
QUERIES = [q.strip() for q in os.getenv("QUERIES", "linen shirt,linen clothing,pure linen,linen fabric,linen kurta,linen brands").split(",") if q.strip()]

# Subreddits to search within
SUBREDDITS = [s.strip() for s in os.getenv("SUBREDDITS", "malefashionadvice,femalefashionadvice,fashion,india,streetwear,frugalmalefashion").split(",") if s.strip()]

# Email config
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO   = os.getenv("EMAIL_TO", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# How many posts max per digest
MAX_POSTS = int(os.getenv("MAX_POSTS", "15"))

# Daily send time (24-hour format, e.g. "10:00")
SEND_TIME = os.getenv("SEND_TIME", "10:00")

# SQLite file for dedup tracking
DB_FILE = os.getenv("DB_FILE", "reddit_digest.db")

# Keywords that must appear in a post to be considered linen-related
LINEN_KEYWORDS = [
    "linen", "pure linen", "linen shirt", "linen fabric",
    "linen clothing", "linen kurta", "linen pant", "linen trouser",
    "linen suit", "linen dress", "linen blend",
]
