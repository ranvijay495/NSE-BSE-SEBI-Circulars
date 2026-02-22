# SOP: RSS Fetcher

## Goal
Fetch the latest newsletters from The Rundown AI's RSS feed.

## Input
- RSS feed URL from `.env` (`RSS_FEED_URL`)

## Output
- List of parsed RSS items, each containing: title, subtitle, author, published_at, source_url, featured_image_url, html_content

## Logic
1. Use `feedparser` to parse the RSS feed URL.
2. For each entry in `feed.entries`:
   - Extract `title`, `description` (subtitle), `dc:creator` (author)
   - Parse `published_parsed` into ISO 8601 timestamp
   - Extract `link` as source_url
   - Extract `enclosure.url` as featured_image_url (if present)
   - Extract `content[0].value` as html_content (this is `content:encoded`)
3. Return list of dicts matching the Parsed Shape in gemini.md.

## Edge Cases
- If `content:encoded` is missing, fall back to `description` field.
- If `published_parsed` is None, use current UTC time.
- If feed returns 0 entries, log warning and return empty list.
- SSL warnings from LibreSSL can be ignored (non-blocking).

## Tool
`tools/fetch_rss.py`
