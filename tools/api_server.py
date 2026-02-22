"""
Tool: API Server
FastAPI backend serving regulatory circular data, filters, bookmarks, and PDF proxy.
"""

import os
import requests as http_requests
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI(title="Regulatory Circular Aggregator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard')

PDF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
}


def get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_URL or SUPABASE_SERVICE_KEY not configured",
        )
    return create_client(url, key)


@app.get("/api/health")
def health_check():
    """Debug endpoint to verify deployment and env vars."""
    return {
        "status": "ok",
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "supabase_key_set": bool(os.getenv("SUPABASE_SERVICE_KEY")),
    }


@app.get("/api/circulars")
def list_circulars(
    source: str = Query(default=None, description="Filter by source: SEBI, BSE, NSE"),
    days: int = Query(default=14, ge=1, le=90),
    from_date: str = Query(default=None, description="Start date YYYY-MM-DD"),
    to_date: str = Query(default=None, description="End date YYYY-MM-DD"),
    category: str = Query(default=None, description="Filter by category"),
):
    """List circulars with optional source, date range, and category filters."""
    client = get_client()

    if from_date and to_date:
        cutoff_start = from_date
        cutoff_end = to_date
    else:
        cutoff_start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cutoff_end = datetime.now().strftime("%Y-%m-%d")

    query = (
        client.table("circulars")
        .select("*")
        .gte("published_date", cutoff_start)
        .lte("published_date", cutoff_end)
        .order("published_date", desc=True)
    )

    if source:
        query = query.eq("source", source.upper())

    if category:
        query = query.eq("category", category)

    result = query.execute()

    # Annotate with bookmark status
    bookmarks_result = client.table("bookmarks").select("circular_id").execute()
    bookmarked_ids = set(b["circular_id"] for b in bookmarks_result.data)

    for circular in result.data:
        circular["is_bookmarked"] = circular["id"] in bookmarked_ids

    return {
        "circulars": result.data,
        "total": len(result.data),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/categories")
def list_categories():
    """Get distinct category values from all circulars."""
    client = get_client()
    result = client.table("circulars").select("category").execute()
    categories = sorted(set(
        row["category"] for row in result.data
        if row.get("category") and row["category"].strip()
    ))
    return {"categories": categories}


@app.get("/api/circulars/{circular_id}")
def get_circular(circular_id: str):
    """Get a single circular by ID."""
    client = get_client()
    result = (
        client.table("circulars")
        .select("*")
        .eq("id", circular_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Circular not found")
    return result.data[0]


@app.get("/api/circulars/{circular_id}/pdf")
def download_pdf(
    circular_id: str,
    mode: str = Query(default="download", description="'view' for inline, 'download' for attachment"),
):
    """Proxy-download the PDF from the original regulatory website."""
    client = get_client()
    result = (
        client.table("circulars")
        .select("title, pdf_url, source")
        .eq("id", circular_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Circular not found")

    circular = result.data[0]
    pdf_url = circular.get("pdf_url")
    if not pdf_url:
        raise HTTPException(status_code=404, detail="No PDF available for this circular")

    headers = dict(PDF_HEADERS)
    source = circular["source"]
    if source == "NSE":
        headers["Referer"] = "https://www.nseindia.com/"
        headers["Accept-Language"] = "en-US,en;q=0.9"
    elif source == "BSE":
        headers["Referer"] = "https://www.bseindia.com/"
    elif source == "SEBI":
        headers["Referer"] = "https://www.sebi.gov.in/"

    try:
        session = http_requests.Session()
        session.headers.update(headers)
        if source == "NSE":
            session.get("https://www.nseindia.com/", timeout=10)

        resp = session.get(pdf_url, timeout=30, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "application/pdf")
        safe_title = "".join(c for c in circular["title"] if c.isalnum() or c in " -_")[:60]

        # Detect file extension from URL
        if pdf_url.endswith(".zip"):
            ext = ".zip"
            content_type = "application/zip"
        elif pdf_url.endswith(".pdf"):
            ext = ".pdf"
            content_type = "application/pdf"
        else:
            ext = ".pdf"

        filename = f"{safe_title}{ext}"

        # ZIPs can't be viewed inline — always force download
        if ext == ".zip" or mode == "download":
            disposition = f'attachment; filename="{filename}"'
        else:
            disposition = f'inline; filename="{filename}"'

        return StreamingResponse(
            resp.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={"Content-Disposition": disposition},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch PDF: {str(e)}")


@app.get("/api/stats")
def get_stats():
    """Get circular counts per source."""
    client = get_client()
    cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    stats = {}
    for source in ["SEBI", "BSE", "NSE"]:
        result = (
            client.table("circulars")
            .select("id", count="exact")
            .eq("source", source)
            .gte("published_date", cutoff)
            .execute()
        )
        stats[source] = result.count if result.count else 0

    stats["total"] = sum(stats.values())
    stats["last_updated"] = datetime.now(timezone.utc).isoformat()
    return stats


# === Bookmark endpoints ===

@app.get("/api/bookmarks")
def list_bookmarks():
    """Get all bookmarked circulars."""
    client = get_client()
    bookmarks_result = (
        client.table("bookmarks")
        .select("circular_id, created_at")
        .order("created_at", desc=True)
        .execute()
    )

    if not bookmarks_result.data:
        return {"bookmarks": [], "total": 0}

    circular_ids = [b["circular_id"] for b in bookmarks_result.data]
    circulars_result = (
        client.table("circulars")
        .select("*")
        .in_("id", circular_ids)
        .execute()
    )

    circular_map = {c["id"]: c for c in circulars_result.data}
    bookmarks = []
    for b in bookmarks_result.data:
        circular = circular_map.get(b["circular_id"])
        if circular:
            circular["is_bookmarked"] = True
            circular["bookmarked_at"] = b["created_at"]
            bookmarks.append(circular)

    return {"bookmarks": bookmarks, "total": len(bookmarks)}


@app.post("/api/bookmarks/{circular_id}")
def add_bookmark(circular_id: str):
    """Bookmark a circular."""
    client = get_client()
    circular = client.table("circulars").select("id").eq("id", circular_id).execute()
    if not circular.data:
        raise HTTPException(status_code=404, detail="Circular not found")

    try:
        client.table("bookmarks").upsert(
            {"circular_id": circular_id},
            on_conflict="circular_id",
        ).execute()
        return {"status": "bookmarked", "circular_id": circular_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bookmark: {str(e)}")


@app.delete("/api/bookmarks/{circular_id}")
def remove_bookmark(circular_id: str):
    """Remove a bookmark."""
    client = get_client()
    client.table("bookmarks").delete().eq("circular_id", circular_id).execute()
    return {"status": "removed", "circular_id": circular_id}


# === Dashboard serving ===

@app.get("/")
def serve_dashboard():
    index_path = os.path.join(DASHBOARD_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Dashboard not built yet</h1>")


if os.path.exists(DASHBOARD_DIR):
    app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
