"""
Tool: NSE Circular Scraper
Fetches circulars from NSE India via their internal JSON API.
Uses session-first cookie pattern to handle Akamai Bot Manager.
"""

import time
import requests
from datetime import datetime, timedelta

NSE_BASE = "https://www.nseindia.com"
CIRCULARS_API = "/api/circulars"
ARCHIVES_BASE = "https://nsearchives.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/companies-listing/circular-for-listed-companies-equity-market",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
}


def scrape_nse(days=7):
    """
    Scrape NSE circulars from the last `days` days.
    Returns list of dicts matching the standard circular shape.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Acquire Akamai cookies by visiting homepage
    try:
        session.get(NSE_BASE + "/", timeout=10)
        time.sleep(1)
    except Exception as e:
        print(f"[NSE] Failed to acquire cookies: {e}")
        return []

    # Step 2: Call circulars API
    today = datetime.now()
    from_date = today - timedelta(days=days)

    params = {
        "from_date": from_date.strftime("%d-%m-%Y"),
        "to_date": today.strftime("%d-%m-%Y"),
    }

    data = _fetch_with_retry(session, NSE_BASE + CIRCULARS_API, params)
    if data is None:
        return []

    # Step 3: Parse response
    circulars = []

    # NSE API returns {"data": [...], "fromDate": ..., "toDate": ...}
    items = data.get("data", []) if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []

    for item in items:
        # Actual NSE field names (confirmed from API response):
        # sub, cirDate, cirDisplayDate, circFilelink, circDisplayNo,
        # circCategory, circDepartment, circFilename, fileExt
        title = item.get("sub", "Untitled")
        date_str = item.get("cirDisplayDate") or item.get("cirDate", "")
        dept = item.get("circDepartment", "")
        category = item.get("circCategory", "")
        ref_no = item.get("circDisplayNo", "")
        pdf_url = item.get("circFilelink", "")

        # Parse date (cirDate is "20260220" format, cirDisplayDate is "February 20, 2026")
        published_date = _parse_nse_date(date_str)

        # Ensure PDF URL is absolute
        if pdf_url and not pdf_url.startswith("http"):
            pdf_url = ARCHIVES_BASE + pdf_url

        circulars.append({
            "source": "NSE",
            "title": title,
            "circular_number": ref_no,
            "published_date": published_date,
            "detail_url": pdf_url or "",
            "pdf_url": pdf_url or None,
            "category": category,
            "department": dept,
        })

    return circulars


def _fetch_with_retry(session, url, params, max_retries=3):
    """Fetch URL with retry on 403 (re-acquire cookies)."""
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                print(f"[NSE] Got 403, re-acquiring cookies (attempt {attempt + 1}/{max_retries})")
                session.cookies.clear()
                session.get(NSE_BASE + "/", timeout=10)
                time.sleep(2)
            else:
                print(f"[NSE] Unexpected status: {resp.status_code}")
                return None
        except requests.exceptions.JSONDecodeError:
            print(f"[NSE] Invalid JSON response (attempt {attempt + 1})")
            time.sleep(1)
        except Exception as e:
            print(f"[NSE] Request failed: {e}")
            time.sleep(1)

    print("[NSE] All retries exhausted")
    return None


def _parse_nse_date(text):
    """Parse various NSE date formats."""
    if not text:
        return datetime.now().strftime("%Y-%m-%d")
    # Handle compact format "20260220"
    if len(text.strip()) == 8 and text.strip().isdigit():
        try:
            return datetime.strptime(text.strip(), "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            pass
    formats = ["%B %d, %Y", "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%d-%B-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d")


if __name__ == "__main__":
    print("[NSE] Scraping circulars from last 14 days...")
    results = scrape_nse(days=14)
    print(f"[NSE] Found {len(results)} circulars")
    for c in results[:10]:
        pdf_status = "PDF" if c["pdf_url"] else "NO-PDF"
        print(f"  [{pdf_status}] {c['published_date']} | {c['title'][:70]}")
