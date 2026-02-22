"""
Phase 2 Handshake — Verify all external service connections.
Run this script to confirm Supabase and RSS feed are reachable.
"""

import os
import sys
import feedparser
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def check_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return False, "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env"
    try:
        client = create_client(url, key)
        result = client.table("circulars").select("id").limit(1).execute()
        return True, f"Supabase connected. Table 'circulars' accessible."
    except Exception as e:
        return False, f"Supabase error: {e}"

def check_rss():
    url = os.getenv("RSS_FEED_URL")
    if not url:
        return False, "Missing RSS_FEED_URL in .env"
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return False, f"RSS parse error: {feed.bozo_exception}"
        title = feed.feed.get("title", "Unknown")
        count = len(feed.entries)
        return True, f"RSS feed '{title}' fetched. {count} entries available."
    except Exception as e:
        return False, f"RSS error: {e}"

def main():
    print("=" * 50)
    print("  PHASE 2 HANDSHAKE — Connection Verification")
    print("=" * 50)

    checks = [
        ("Supabase", check_supabase),
        ("RSS Feed", check_rss),
    ]

    all_ok = True
    for name, fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"\n  [{status}] {name}")
        print(f"         {msg}")
        if not ok:
            all_ok = False

    print("\n" + "=" * 50)
    if all_ok:
        print("  ALL CHECKS PASSED — Ready for Phase 3")
    else:
        print("  SOME CHECKS FAILED — Fix before proceeding")
    print("=" * 50)
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
