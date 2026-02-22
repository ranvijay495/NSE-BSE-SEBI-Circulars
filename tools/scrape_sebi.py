"""
Tool: SEBI Circular Scraper
Fetches circulars from SEBI via AJAX endpoint.
Requires session cookie (JSESSIONID) from listing page.
"""

import re
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup

LISTING_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
AJAX_URL = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp"
BASE_URL = "https://www.sebi.gov.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_sebi(days=7):
    """
    Scrape SEBI circulars from the last `days` days.
    Returns list of dicts: {title, circular_number, published_date, detail_url, pdf_url, category, department}
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Get session cookie
    session.get(LISTING_URL, timeout=15)

    # Step 2: Query by date range
    today = datetime.now()
    from_date = today - timedelta(days=days)

    form_data = {
        "nextValue": "1",
        "next": "s",
        "search": "",
        "fromDate": from_date.strftime("%d-%m-%Y"),
        "toDate": today.strftime("%d-%m-%Y"),
        "fromYear": "",
        "toYear": "",
        "deptId": "-1",
        "sid": "1",
        "ssid": "7",
        "smid": "0",
        "ssidhidden": "7",
        "intmid": "-1",
        "sText": "Legal",
        "ssText": "Circulars",
        "smText": "",
        "doDirect": "-1",
    }

    resp = session.post(
        AJAX_URL,
        data=form_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LISTING_URL,
        },
        timeout=15,
    )

    if resp.status_code == 530:
        # Re-establish session
        session.get(LISTING_URL, timeout=15)
        resp = session.post(AJAX_URL, data=form_data, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LISTING_URL,
        }, timeout=15)

    # Step 3: Parse HTML response (split by #@#, take first fragment)
    html_content = resp.text.split("#@#")[0]
    soup = BeautifulSoup(html_content, "lxml")

    circulars = []
    rows = soup.select("tr[role='row']")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        date_text = cells[0].get_text(strip=True)
        link = cells[1].find("a")
        if not link:
            continue

        title = link.get_text(strip=True)
        detail_url = link.get("href", "")
        if detail_url and not detail_url.startswith("http"):
            detail_url = urljoin(BASE_URL, detail_url)

        # Parse date
        try:
            published_date = datetime.strptime(date_text, "%b %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            published_date = datetime.now().strftime("%Y-%m-%d")

        circulars.append({
            "source": "SEBI",
            "title": title,
            "circular_number": _extract_id_from_url(detail_url),
            "published_date": published_date,
            "detail_url": detail_url,
            "pdf_url": None,  # Will be extracted from detail page
            "category": "Circular",
            "department": "SEBI",
        })

    # Step 4: Extract PDF URLs from detail pages
    for circular in circulars:
        if circular["detail_url"]:
            try:
                pdf_url = _extract_pdf_url(session, circular["detail_url"])
                circular["pdf_url"] = pdf_url
                time.sleep(0.5)  # Rate limit
            except Exception as e:
                print(f"  [SEBI] Failed to get PDF for: {circular['title'][:50]} — {e}")

    return circulars


def _extract_id_from_url(url):
    """Extract circular ID from URL like ..._99814.html"""
    match = re.search(r'_(\d+)\.html', url)
    return match.group(1) if match else None


def _extract_pdf_url(session, detail_url):
    """Fetch detail page and extract PDF URL from iframe."""
    resp = session.get(detail_url, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    iframe = soup.find("iframe")
    if iframe and iframe.get("src"):
        src = iframe["src"]
        parsed = urlparse(src)
        file_param = parse_qs(parsed.query).get("file", [None])[0]
        if file_param:
            return file_param

    # Fallback: look for direct PDF links
    for a in soup.find_all("a", href=True):
        if a["href"].endswith(".pdf"):
            href = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            return href

    return None


if __name__ == "__main__":
    print("[SEBI] Scraping circulars from last 14 days...")
    results = scrape_sebi(days=14)
    print(f"[SEBI] Found {len(results)} circulars")
    for c in results:
        pdf_status = "PDF" if c["pdf_url"] else "NO-PDF"
        print(f"  [{pdf_status}] {c['published_date']} | {c['title'][:70]}")
