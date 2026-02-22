"""
Tool: BSE Circular Scraper
Fetches circulars from BSE India via their JSON API and ASP.NET detail pages.
"""

import re
import time
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

API_URL = "https://api.bseindia.com/BseIndiaAPI/api/GetDataCirToListComp/w"
DETAIL_BASE = "https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page="
BSE_BASE = "https://www.bseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/corporates/CirularToListedComp.html",
    "Origin": "https://www.bseindia.com",
}


def scrape_bse(days=7):
    """
    Scrape BSE circulars from the last `days` days.
    Uses BSE JSON API for listing, then scrapes detail pages for PDF links.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Visit BSE main page for cookies
    try:
        session.get(BSE_BASE + "/", timeout=10, headers={
            "User-Agent": HEADERS["User-Agent"],
            "Accept": "text/html",
        })
    except Exception:
        pass

    time.sleep(0.5)

    # Step 2: Call JSON API
    try:
        resp = session.get(API_URL, timeout=15)
        if resp.status_code == 301:
            # Redirect — try with explicit headers
            resp = session.get(API_URL, timeout=15, headers={
                "Referer": "https://www.bseindia.com/corporates/CirularToListedComp.html",
                "Origin": "https://www.bseindia.com",
                "Accept": "application/json",
            })
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[BSE] API request failed: {e}")
        print("[BSE] Falling back to ASP.NET scraping...")
        return _scrape_bse_aspnet(session, days)

    # Step 3: Parse JSON response
    # API returns {"Table": [...]} where each item has mr_heading, mr_date, articleid
    items = data.get("Table", []) if isinstance(data, dict) else data
    if not isinstance(items, list):
        print(f"[BSE] Unexpected response format: {type(data)}")
        return _scrape_bse_aspnet(session, days)

    cutoff = datetime.now() - timedelta(days=days)
    circulars = []

    for item in items:
        title = item.get("mr_heading", "Untitled")
        date_str = item.get("mr_date", "")
        notice_id = item.get("articleid", "")

        published_date = _parse_bse_date(date_str)

        # Filter by date
        try:
            pub_dt = datetime.strptime(published_date, "%Y-%m-%d")
            if pub_dt < cutoff:
                continue
        except ValueError:
            pass

        detail_url = DETAIL_BASE + str(notice_id) if notice_id else ""

        circulars.append({
            "source": "BSE",
            "title": title,
            "circular_number": str(notice_id),
            "published_date": published_date,
            "detail_url": detail_url,
            "pdf_url": None,
            "category": "Circular",
            "department": "BSE",
        })

    # Step 4: Extract PDF URLs from detail pages (limit to avoid rate limiting)
    for circular in circulars:
        if circular["detail_url"]:
            try:
                pdf_url = _extract_pdf_url(session, circular["detail_url"])
                circular["pdf_url"] = pdf_url
                time.sleep(0.3)
            except Exception as e:
                print(f"  [BSE] Failed PDF for: {circular['title'][:50]} — {e}")

    return circulars


def _scrape_bse_aspnet(session, days):
    """Fallback: scrape BSE via ASP.NET NoticesCirculars page."""
    listing_url = "https://www.bseindia.com/markets/MarketInfo/NoticesCirculars.aspx"

    resp = session.get(listing_url, timeout=15, headers={
        "Accept": "text/html,application/xhtml+xml",
    })
    soup = BeautifulSoup(resp.text, "lxml")

    viewstate = _get_field(soup, "__VIEWSTATE")
    viewstate_gen = _get_field(soup, "__VIEWSTATEGENERATOR")
    event_validation = _get_field(soup, "__EVENTVALIDATION")

    if not viewstate:
        print("[BSE] Failed to extract ViewState tokens")
        return []

    today = datetime.now()
    from_date = today - timedelta(days=days)

    form_data = {
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstate_gen,
        "__EVENTVALIDATION": event_validation,
        "ctl00$ContentPlaceHolder1$rdbPeriod": "rdbPeriod",
        "ctl00$ContentPlaceHolder1$txtFromDt": from_date.strftime("%d/%m/%Y"),
        "ctl00$ContentPlaceHolder1$txtToDate": today.strftime("%d/%m/%Y"),
        "ctl00$ContentPlaceHolder1$ddlSegName": "",
        "ctl00$ContentPlaceHolder1$ddlCategoryName": "",
        "ctl00$ContentPlaceHolder1$btnSubmit": "Submit",
    }

    resp = session.post(listing_url, data=form_data, headers={
        "Referer": listing_url,
        "Accept": "text/html",
    }, timeout=30)

    soup = BeautifulSoup(resp.text, "lxml")
    circulars = []

    for row in soup.select("table tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        link = row.find("a")
        if not link:
            continue

        title = link.get_text(strip=True)
        href = link.get("href", "")
        notice_match = re.search(r'page=([^&]+)', href)
        notice_id = notice_match.group(1) if notice_match else ""

        circulars.append({
            "source": "BSE",
            "title": title,
            "circular_number": notice_id,
            "published_date": datetime.now().strftime("%Y-%m-%d"),
            "detail_url": DETAIL_BASE + notice_id if notice_id else "",
            "pdf_url": None,
            "category": "Circular",
            "department": "BSE",
        })

    return circulars


def _get_field(soup, name):
    field = soup.find("input", {"name": name})
    return field.get("value", "") if field else ""


def _parse_bse_date(text):
    """Parse various BSE date formats."""
    if not text:
        return datetime.now().strftime("%Y-%m-%d")
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y", "%Y-%m-%d",
               "%m/%d/%Y", "%b %d, %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d")


def _extract_pdf_url(session, detail_url):
    """Fetch BSE detail page and extract PDF download link."""
    if not detail_url:
        return None

    resp = session.get(detail_url, timeout=15, headers={
        "Accept": "text/html",
        "User-Agent": HEADERS["User-Agent"],
    })
    soup = BeautifulSoup(resp.text, "lxml")

    # Look for DownloadAttach.aspx links
    for a in soup.find_all("a", href=True):
        if "DownloadAttach" in a["href"]:
            href = a["href"]
            if not href.startswith("http"):
                href = BSE_BASE + href
            return href

    # Look for direct PDF/zip links
    for a in soup.find_all("a", href=True):
        if a["href"].endswith((".pdf", ".zip")):
            href = a["href"]
            if not href.startswith("http"):
                href = BSE_BASE + href
            return href

    return None


if __name__ == "__main__":
    print("[BSE] Scraping circulars from last 14 days...")
    results = scrape_bse(days=14)
    print(f"[BSE] Found {len(results)} circulars")
    for c in results[:10]:
        pdf_status = "PDF" if c["pdf_url"] else "NO-PDF"
        print(f"  [{pdf_status}] {c['published_date']} | {c['title'][:70]}")
