# SOP: API Server

## Goal
Serve dashboard data and PDF downloads via a FastAPI backend.

## Endpoints

### GET /api/newsletters
- Returns list of newsletters from Supabase (last 24h by default)
- Query params: `hours` (int, default 24), `limit` (int, default 20)
- Response: {newsletters: [...], total: int, last_updated: timestamp}

### GET /api/newsletters/{id}
- Returns full newsletter with stories, quick_hits, trending_tools
- Response: full newsletter object per gemini.md schema

### GET /api/newsletters/{id}/pdf
- Generates and streams PDF for a specific newsletter
- Content-Type: application/pdf
- Content-Disposition: attachment; filename="{title}.pdf"

### GET /
- Serves the static dashboard (index.html)

## Logic
1. Load Supabase client using service_role key from `.env`.
2. Query newsletters table with time filter.
3. For detail view, join stories/quick_hits/trending_tools by newsletter_id.
4. For PDF, fetch html_content and pass to generate_pdf tool.

## Tool
`tools/api_server.py`
