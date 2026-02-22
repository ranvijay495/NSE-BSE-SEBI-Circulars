# SOP: PDF Generator

## Goal
Convert a newsletter's HTML content into a downloadable PDF file.

## Input
- Newsletter HTML content (from Supabase or RSS)
- Newsletter title (for filename)

## Output
- PDF file bytes or saved to `.tmp/{newsletter_id}.pdf`

## Logic
1. Wrap the raw HTML in a minimal HTML document with proper `<head>` and CSS.
2. Inject base styles for readability (max-width, font, spacing).
3. Use WeasyPrint to render HTML to PDF.
4. Return PDF bytes for streaming or save to `.tmp/`.

## Edge Cases
- External images may fail to load — set a timeout on resource fetching.
- Very long newsletters may need page breaks — use CSS `page-break-before`.
- If WeasyPrint fails, log error and return None.

## Tool
`tools/generate_pdf.py`
