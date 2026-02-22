"""
Modal Scheduled Scraper
Runs the SEBI/BSE/NSE scraping pipeline daily at 7:00 AM IST (1:30 AM UTC).
Deploy: python3 -m modal deploy tools/modal_scheduler.py
"""

import os
import modal

app = modal.App("nse-bse-sebi-scraper")

tools_dir = os.path.dirname(os.path.abspath(__file__))

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "requests",
        "beautifulsoup4",
        "lxml",
        "supabase",
        "python-dotenv",
    )
    .add_local_dir(tools_dir, remote_path="/root/tools")
)

supabase_secret = modal.Secret.from_name("supabase-credentials")


@app.function(
    image=image,
    secrets=[supabase_secret],
    timeout=600,
    schedule=modal.Cron("30 1 * * *"),  # 1:30 AM UTC = 7:00 AM IST
)
def run_scraper():
    """Scheduled scraper — runs daily at 7 AM IST."""
    import sys
    import time

    sys.path.insert(0, "/root/tools")

    from scrape_sebi import scrape_sebi
    from scrape_bse import scrape_bse
    from scrape_nse import scrape_nse
    from store_circulars import store_circulars

    days = 14
    print(f"[Modal] Pipeline started — scraping last {days} days\n")

    results = {}

    # SEBI
    print("[Modal] === SEBI ===")
    try:
        sebi = scrape_sebi(days=days)
        print(f"[Modal] SEBI: scraped {len(sebi)} circulars")
        ins, skip = store_circulars(sebi)
        results["SEBI"] = {"scraped": len(sebi), "stored": ins, "skipped": skip}
        print(f"[Modal] SEBI: {ins} stored, {skip} skipped")
    except Exception as e:
        print(f"[Modal] SEBI failed: {e}")
        results["SEBI"] = {"error": str(e)}

    time.sleep(2)

    # BSE
    print("\n[Modal] === BSE ===")
    try:
        bse = scrape_bse(days=days)
        print(f"[Modal] BSE: scraped {len(bse)} circulars")
        ins, skip = store_circulars(bse)
        results["BSE"] = {"scraped": len(bse), "stored": ins, "skipped": skip}
        print(f"[Modal] BSE: {ins} stored, {skip} skipped")
    except Exception as e:
        print(f"[Modal] BSE failed: {e}")
        results["BSE"] = {"error": str(e)}

    time.sleep(2)

    # NSE
    print("\n[Modal] === NSE ===")
    try:
        nse = scrape_nse(days=days)
        print(f"[Modal] NSE: scraped {len(nse)} circulars")
        ins, skip = store_circulars(nse)
        results["NSE"] = {"scraped": len(nse), "stored": ins, "skipped": skip}
        print(f"[Modal] NSE: {ins} stored, {skip} skipped")
    except Exception as e:
        print(f"[Modal] NSE failed: {e}")
        results["NSE"] = {"error": str(e)}

    # Summary
    print("\n[Modal] === DONE ===")
    for source, r in results.items():
        if "error" in r:
            print(f"  {source}: FAILED — {r['error'][:80]}")
        else:
            print(f"  {source}: {r['scraped']} scraped, {r['stored']} stored, {r['skipped']} skipped")

    return results
