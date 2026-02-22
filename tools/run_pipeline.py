"""
Tool: Pipeline Orchestrator
Scrapes circulars from SEBI, BSE, and NSE, then stores in Supabase.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from scrape_sebi import scrape_sebi
from scrape_bse import scrape_bse
from scrape_nse import scrape_nse
from store_circulars import store_circulars


def run(days=14):
    """Run the full scrape → store pipeline for all 3 sources."""
    print(f"[Pipeline] Scraping circulars from last {days} days...\n")

    results = {}

    # SEBI
    print("[Pipeline] === SEBI ===")
    try:
        sebi = scrape_sebi(days=days)
        print(f"[Pipeline] SEBI: scraped {len(sebi)} circulars")
        ins, skip = store_circulars(sebi)
        results["SEBI"] = {"scraped": len(sebi), "stored": ins, "skipped": skip}
        print(f"[Pipeline] SEBI: {ins} stored, {skip} skipped")
    except Exception as e:
        print(f"[Pipeline] SEBI failed: {e}")
        results["SEBI"] = {"scraped": 0, "stored": 0, "skipped": 0, "error": str(e)}

    time.sleep(2)

    # BSE
    print("\n[Pipeline] === BSE ===")
    try:
        bse = scrape_bse(days=days)
        print(f"[Pipeline] BSE: scraped {len(bse)} circulars")
        ins, skip = store_circulars(bse)
        results["BSE"] = {"scraped": len(bse), "stored": ins, "skipped": skip}
        print(f"[Pipeline] BSE: {ins} stored, {skip} skipped")
    except Exception as e:
        print(f"[Pipeline] BSE failed: {e}")
        results["BSE"] = {"scraped": 0, "stored": 0, "skipped": 0, "error": str(e)}

    time.sleep(2)

    # NSE
    print("\n[Pipeline] === NSE ===")
    try:
        nse = scrape_nse(days=days)
        print(f"[Pipeline] NSE: scraped {len(nse)} circulars")
        ins, skip = store_circulars(nse)
        results["NSE"] = {"scraped": len(nse), "stored": ins, "skipped": skip}
        print(f"[Pipeline] NSE: {ins} stored, {skip} skipped")
    except Exception as e:
        print(f"[Pipeline] NSE failed: {e}")
        results["NSE"] = {"scraped": 0, "stored": 0, "skipped": 0, "error": str(e)}

    # Summary
    total_scraped = sum(r["scraped"] for r in results.values())
    total_stored = sum(r["stored"] for r in results.values())
    print(f"\n[Pipeline] === DONE ===")
    print(f"[Pipeline] Total: {total_scraped} scraped, {total_stored} stored")
    for source, r in results.items():
        status = f"{r['scraped']} scraped, {r['stored']} stored"
        if "error" in r:
            status += f" (ERROR: {r['error'][:50]})"
        print(f"  {source}: {status}")

    return results


if __name__ == "__main__":
    days = 14
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass
    run(days=days)
