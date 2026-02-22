"""
Tool: Circular Storage
Upserts scraped circulars into Supabase `circulars` table.
Skips duplicates via UNIQUE(source, detail_url) constraint.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    return create_client(url, key)


def store_circulars(circulars):
    """
    Upsert a list of circular dicts into Supabase.
    Returns (inserted, skipped) counts.
    """
    if not circulars:
        return 0, 0

    client = get_client()
    inserted = 0
    skipped = 0

    for c in circulars:
        row = {
            "source": c["source"],
            "title": c["title"],
            "circular_number": c.get("circular_number"),
            "published_date": c["published_date"],
            "detail_url": c.get("detail_url", ""),
            "pdf_url": c.get("pdf_url"),
            "category": c.get("category", ""),
            "department": c.get("department", ""),
        }

        try:
            client.table("circulars").upsert(
                row,
                on_conflict="source,detail_url",
            ).execute()
            inserted += 1
        except Exception as e:
            err_msg = str(e)
            if "duplicate" in err_msg.lower() or "conflict" in err_msg.lower():
                skipped += 1
            else:
                print(f"  [Store] Error: {c['title'][:50]} — {e}")
                skipped += 1

    return inserted, skipped


if __name__ == "__main__":
    print("[Store] Testing connection...")
    client = get_client()
    result = client.table("circulars").select("id", count="exact").execute()
    print(f"[Store] Circulars in DB: {result.count}")
