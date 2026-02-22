# task_plan.md — Project Blueprint

> Phases, goals, and checklists. Updated at each phase transition.

---

## Current Phase: 🟡 Phase 1 — Blueprint (Awaiting Approval)

### Phase 0 Checklist (Complete)

- [x] Workspace created
- [x] `gemini.md` initialized
- [x] `task_plan.md` initialized
- [x] `findings.md` initialized
- [x] `progress.md` initialized
- [x] Discovery Questions answered
- [x] Data Schema defined in `gemini.md`
- [ ] **Blueprint approved by user** ← YOU ARE HERE

---

## Phases Overview

| Phase | Name | Status |
|-------|------|--------|
| 0 | Initialization | ✅ Complete |
| 1 | Blueprint (Vision & Logic) | 🟡 Awaiting Approval |
| 2 | Link (Connectivity) | 🔴 Not Started |
| 3 | Architect (3-Layer Build) | 🔴 Not Started |
| 4 | Stylize (Refinement & UI) | 🔴 Not Started |
| 5 | Trigger (Deployment) | 🔴 Not Started |

---

## Goal

Build a **Newsletter Aggregator Dashboard** that:
- Collects The Rundown AI newsletters from the past 24 hours via RSS
- Stores parsed content in Supabase
- Displays newsletters on a branded web dashboard
- Allows PDF download of each newsletter

---

## Blueprint

### Architecture Overview

```
RSS Feed (beehiiv) → Python Scraper → Supabase DB → Web Dashboard (HTML/CSS/JS)
                                                      ↓
                                                  PDF Generator
```

### Phase 2: Link (Connectivity)
- [ ] Verify Supabase credentials (`.env`)
- [ ] Test RSS feed fetch (`https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml`)
- [ ] Create Supabase tables (newsletters, stories, quick_hits, trending_tools)
- [ ] Handshake scripts in `tools/` confirming both services respond

### Phase 3: Architect (3-Layer Build)

**Layer 1 — Architecture (SOPs in `architecture/`)**
- [ ] `architecture/rss_fetcher.md` — How to fetch and parse RSS
- [ ] `architecture/html_parser.md` — How to extract stories from HTML
- [ ] `architecture/pdf_generator.md` — How to convert newsletter to PDF
- [ ] `architecture/api_server.md` — How the dashboard API works
- [ ] `architecture/dashboard.md` — Frontend structure and routes

**Layer 3 — Tools (Scripts in `tools/`)**
- [ ] `tools/fetch_rss.py` — Fetch RSS feed, return parsed items
- [ ] `tools/parse_newsletter.py` — Extract stories, quick hits, tools from HTML
- [ ] `tools/store_to_supabase.py` — Upsert parsed data into Supabase
- [ ] `tools/generate_pdf.py` — Convert newsletter HTML to downloadable PDF
- [ ] `tools/api_server.py` — Flask/FastAPI server for dashboard API
- [ ] `tools/run_pipeline.py` — Orchestrator: fetch → parse → store (daily trigger)

**Frontend**
- [ ] `dashboard/index.html` — Main dashboard page
- [ ] `dashboard/style.css` — Brand-compliant styles
- [ ] `dashboard/app.js` — Fetch API data, render cards, handle PDF download

### Phase 4: Stylize (Refinement & UI)
- [ ] Apply brand colors (#0C4DA2, #19579B, #E0E0E0, #E30514)
- [ ] Apply San Francisco font stack with web fallbacks
- [ ] Professional layout: newsletter cards with title, date, story count, download button
- [ ] Dark theme variant (per reference image)
- [ ] User feedback round

### Phase 5: Trigger (Deployment)
- [ ] Deploy dashboard to hosting (Vercel / Supabase Edge / local server)
- [ ] Set up daily cron job or scheduler for RSS pipeline
- [ ] Finalize Maintenance Log in `gemini.md`

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Data Source | beehiiv RSS feed (feedparser) |
| HTML Parsing | BeautifulSoup4 |
| Database | Supabase (PostgreSQL) |
| Backend API | FastAPI (Python) |
| PDF Generation | WeasyPrint or pdfkit |
| Frontend | Vanilla HTML/CSS/JS |
| Scheduling | cron / APScheduler |

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| RSS feed changes format | Parser has fallback; HTML structure logged in findings.md |
| RSS only returns recent items | Sitemap fallback for historical data |
| Cloudflare blocks scraping | RSS is on separate domain (rss.beehiiv.com), no protection |
| PDF rendering issues | Use WeasyPrint for CSS-aware rendering; test with real content |
| San Francisco font unavailable | System font stack fallback in CSS |
