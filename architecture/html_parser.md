# SOP: HTML Parser

## Goal
Extract structured stories, quick hits, and trending tools from newsletter HTML.

## Input
- Raw HTML string from `content:encoded` field of RSS item.

## Output
- `stories`: list of {category, headline, summary, details[], why_it_matters, image_url}
- `quick_hits`: list of {title, description, url}
- `trending_tools`: list of {name, description, url}

## Logic
1. Parse HTML with BeautifulSoup (lxml parser).
2. **Stories** — Look for pattern:
   - Category: uppercase text block (e.g., "OPENAI & ANTHROPIC")
   - Headline: link text following category
   - Image: `<img>` within section
   - "The Rundown:" paragraph → summary
   - "The details:" bullet list → details[]
   - "Why it matters:" paragraph → why_it_matters
3. **Quick Hits** — Find section containing "QUICK HITS" header:
   - Trending Tools: items with emoji + tool name + description + link
   - News items: brief one-liners with links
4. Return structured data as dicts.

## Edge Cases
- Not all stories have all fields — set missing fields to None.
- Sponsored content sections should be skipped.
- HTML structure may vary slightly between issues — use flexible matching.
- If parser fails on a section, log warning and continue with remaining sections.

## Tool
`tools/parse_newsletter.py`
