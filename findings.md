# findings.md — Research & Discoveries

> Accumulated knowledge: API quirks, constraints, useful repos, and discoveries.

---

## 2026-02-22: The Rundown AI — Source Research

### Platform
- Hosted on **beehiiv** (newsletter platform)
- CMS: Typedream, Styling: Tailwind CSS
- Bot protection: Cloudflare Turnstile (on main site, NOT on RSS)

### RSS Feed (Primary Data Source)
- **URL:** `https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml`
- **Format:** RSS 2.0 with `content:encoded` containing full HTML
- **Auth:** None required — fully public
- **Fields per item:** title, description, link, guid, pubDate, dc:creator, enclosure (image), content:encoded (full HTML)
- **Publishes:** Daily on weekdays

### Newsletter Structure (per issue)
1. Header with nav links
2. Sponsor banner
3. Welcome/intro box by Rowan Cheung
4. Table of contents (5 topics)
5. **5 main stories** — each with: category label, headline, image, "The Rundown" summary, "The details" bullets, "Why it matters" analysis
6. Mid-newsletter sponsor
7. **Quick Hits** — trending tools (4 items) + brief news (5-6 items)
8. Community section
9. Footer

### HTML Patterns
- Text containers: `<div class="section">`
- Images: `<img class="image__image">`
- Links: `<a class="link" target="_blank">`
- beehiiv classes: `beehiiv__body`, `section`, `paragraph`

### Anti-Scraping
- robots.txt: No blanket disallow. Blocks Amazonbot and Nutch.
- Cloudflare Turnstile on main site pages (login, subscribe).
- RSS feed on `rss.beehiiv.com` has **no bot protection**.

### Archive
- Sitemap: `https://www.therundown.ai/sitemap.xml` — 950+ issue URLs
- Individual issues at: `https://www.therundown.ai/p/{slug}`

---

## Useful GitHub Repos

| Repo | Description |
|------|-------------|
| [Carsoncantcode/newsletter-scraper](https://github.com/Carsoncantcode/newsletter-scraper) | Python API for scraping beehiiv newsletters |
| [Newsletter Scraper (Apify)](https://apify.com/benthepythondev/newsletter-scraper) | Production-grade actor supporting beehiiv, Substack, Ghost |
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | Web Data API — converts sites to LLM-ready markdown |
| [kaiban-ai/kaiban-agents-aggregator](https://github.com/kaiban-ai/kaiban-agents-aggregator) | AI newsletter aggregator (React) — architecture reference |
| [finaldie/auto-news](https://github.com/finaldie/auto-news) | RSS-to-LLM pipeline — architecture reference |

---

## Brand Guidelines Summary

| Property | Value |
|----------|-------|
| Primary | `#0C4DA2` |
| Accent | `#19579B` |
| Background | `#E0E0E0` |
| Text/Links | `#E30514` |
| Font | San Francisco, 16px uniform |
| Spacing | 4px base, 3px border-radius |
| Tone | Professional, medium energy |
| Reference | Dark-themed dashboard mockup (`DesignGuidelines/image.png`) |

---

## Constraints

- beehiiv RSS feed returns most recent items (not full 950+ archive). For history, sitemap scraping needed.
- PDF generation from HTML requires handling images, links, and beehiiv CSS classes.
- San Francisco font is Apple-only system font — web fallback needed (e.g., `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`).

---
