# SOP: Dashboard Frontend

## Goal
Display newsletters in a branded web UI with PDF download buttons.

## Structure
- `dashboard/index.html` — Single page app
- `dashboard/style.css` — Brand-compliant styles
- `dashboard/app.js` — API calls and rendering

## Layout
1. **Header**: Project title + logo area + last updated timestamp
2. **Newsletter Cards Grid**: Each card shows:
   - Title
   - Author + publish date
   - Story count badge
   - Featured image (if available)
   - "Download PDF" button
   - "Read More" expand for stories
3. **Empty State**: "No newsletters in the past 24 hours" message
4. **Footer**: Minimal attribution

## Brand Application
- Primary: #0C4DA2 (headers, buttons)
- Accent: #19579B (hover states, borders)
- Background: #E0E0E0 (page background)
- Text/Links: #E30514 (CTAs, highlights)
- Font: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
- Border radius: 3px
- Spacing unit: 4px

## Tool
Static files served by FastAPI from `dashboard/` directory.
