# gemini.md — Project Constitution

> This file is LAW. Update only when: a schema changes, a rule is added, or architecture is modified.

---

## Project Identity

- **Project Name:** Rundown Aggregator Dashboard
- **System Pilot:** Claude (Opus 4.6)
- **Protocol:** B.L.A.S.T. + A.N.T. 3-Layer Architecture
- **Date Initialized:** 2026-02-21
- **Status:** 🟡 BLUEPRINT — Awaiting Approval

---

## Data Schema

### Input Shape (Raw RSS Item)
```json
{
  "title": "string — Newsletter headline",
  "description": "string — Subtitle/teaser text",
  "link": "string — URL to web version",
  "guid": "string — Unique identifier",
  "pubDate": "string — RFC 2822 date (e.g. 'Thu, 20 Feb 2026 12:00:00 GMT')",
  "creator": "string — Author name",
  "enclosure": {
    "url": "string — Featured image URL",
    "length": "number — File size in bytes",
    "type": "string — MIME type (e.g. 'image/png')"
  },
  "content_encoded": "string — Full HTML of the newsletter issue"
}
```

### Parsed Shape (Stored in Supabase)
```json
{
  "id": "uuid — Primary key",
  "title": "string",
  "subtitle": "string",
  "author": "string",
  "published_at": "timestamp — ISO 8601",
  "source_url": "string",
  "featured_image_url": "string | null",
  "html_content": "text — Full HTML body",
  "scraped_at": "timestamp — When we fetched it",
  "stories": [
    {
      "category": "string — e.g. 'OPENAI & ANTHROPIC'",
      "headline": "string",
      "summary": "string — 'The Rundown' paragraph",
      "details": ["string — Bullet points"],
      "why_it_matters": "string",
      "image_url": "string | null"
    }
  ],
  "quick_hits": [
    {
      "title": "string",
      "description": "string",
      "url": "string"
    }
  ],
  "trending_tools": [
    {
      "name": "string",
      "description": "string",
      "url": "string"
    }
  ]
}
```

### Output Shape (Payload — Dashboard API Response)
```json
{
  "newsletters": [
    {
      "id": "uuid",
      "title": "string",
      "subtitle": "string",
      "author": "string",
      "published_at": "timestamp",
      "featured_image_url": "string | null",
      "story_count": "number",
      "download_url": "/api/newsletter/{id}/pdf"
    }
  ],
  "total": "number",
  "last_updated": "timestamp"
}
```

---

## Behavioral Rules

1. **Read-only source data.** Never modify The Rundown AI's content or interfere with their systems.
2. **RSS-first.** Always prefer the RSS feed over web scraping. Fall back to scraping only if RSS is unavailable.
3. **24-hour window.** The dashboard shows newsletters from the past 24 hours by default.
4. **PDF fidelity.** Downloaded PDFs must preserve the visual structure and readability of the original newsletter.
5. **Fail loudly.** Log and surface all errors — never swallow exceptions silently.
6. **No secrets in code.** All API keys, Supabase credentials, and tokens live in `.env`.

---

## Integrations

| Service | Status | Notes |
|---------|--------|-------|
| Supabase | ❌ Unverified | User confirms credentials ready. Verify in Phase 2. |
| The Rundown AI RSS | ❌ Unverified | `https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml` — public, no auth. |

---

## Brand Guidelines

| Property | Value |
|----------|-------|
| Primary Color | `#0C4DA2` (deep blue) |
| Accent Color | `#19579B` (lighter blue) |
| Background | `#E0E0E0` (light gray) |
| Text Primary / Links | `#E30514` (bold red) |
| Font | San Francisco (system) |
| Font Size (all) | 16px |
| Spacing Unit | 4px |
| Border Radius | 3px |
| Tone | Professional, medium energy |
| Audience | Educational institutions, corporate training |

> Reference image suggests dark-theme dashboard variant may also be desired.

---

## Architectural Invariants

1. No code is written before Blueprint is approved.
2. All intermediate files go to `.tmp/`.
3. Tools are atomic and independently testable.
4. `.env` holds all secrets — never hardcoded.
5. If logic changes, update the SOP in `architecture/` before updating code.
6. RSS feed is the primary data source. Web scraping is a fallback only.
7. Supabase is the single database — no local persistence for production data.

---

## Maintenance Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-21 | Project initialized | System Pilot |
| 2026-02-22 | Discovery complete, Data Schema defined, Brand Guidelines added | System Pilot |
