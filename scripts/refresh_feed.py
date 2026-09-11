#!/usr/bin/env python3
"""
Fetches the latest posts from the Substack RSS feed and bakes the newest
Gazette editions and essays directly into index.html.

This replaces the old client-side approach (direct fetch, then AllOrigins,
then RSS2JSON), which failed for three separate reasons:
  1. Substack's feed has no Access-Control-Allow-Origin header, so a direct
     browser fetch is always blocked by CORS.
  2. AllOrigins is a free public proxy that is frequently slow or down.
  3. RSS2JSON now requires a paid API key to use the `count` parameter,
     which the old code always sent, so that call always failed too.

Running this server-side (in GitHub Actions) sidesteps all three problems:
there's no browser, so no CORS restriction, and no third-party proxy needed.

Run manually with:  python3 scripts/refresh_feed.py
Run automatically via: .github/workflows/refresh-content.yml
"""
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

FEED_URL = "https://ccarazas.substack.com/feed"
INDEX_PATH = "index.html"
GAZETTE_LIMIT = 3
ESSAY_LIMIT = 3
GAZETTE_EXCERPT_LEN = 170
ESSAY_EXCERPT_LEN = 190


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def strip_html(value):
    parser = _TextExtractor()
    parser.feed(value or "")
    text = "".join(parser.parts)
    return re.sub(r"\s+", " ", text).strip()


def escape_html(value):
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def clean_title(value):
    value = value or ""
    value = re.sub(r"[\U0001F300-\U0001FFFF]", "", value)
    value = re.sub(r"[\u2600-\u27BF]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value):
    value = (value or "").replace("\u00a0", " ")
    value = re.sub(r"&amp;", "&", value, flags=re.I)
    value = value.lower().replace("&", " and ")
    return re.sub(r"\s+", " ", value).strip()


def title_is_gazette(title):
    return bool(re.match(
        r"^(?:the\s+)?plymouth\s+sentinel\s+and\s+canine\s+gazette\b",
        normalize_title(title),
    ))


def title_looks_like_live(title, description):
    haystack = normalize_title(f"{title} {description}")
    return bool(re.search(
        r"\bsubstack live\b|\blive with\b|\ba recording from\b", haystack
    ))


def format_date(value):
    try:
        dt = parsedate_to_datetime(value)
        return f"{dt.strftime('%b')} {dt.day}, {dt.year}"
    except Exception:
        return ""


def sort_key(item):
    try:
        return parsedate_to_datetime(item["pubDate"])
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def fetch_feed_items():
    req = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ChrisCarazasSiteBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item"):
        def get(tag):
            el = item.find(tag)
            return el.text if el is not None and el.text else ""
        items.append({
            "title": get("title"),
            "link": get("link"),
            "pubDate": get("pubDate"),
            "description": get("description"),
        })
    return items


def render_gazette_card(p):
    full = strip_html(p["description"])
    excerpt = full[:GAZETTE_EXCERPT_LEN]
    ellipsis = "&hellip;" if len(full) >= GAZETTE_EXCERPT_LEN else ""
    desc = (
        f"<p class='gazette-card-desc'>{escape_html(excerpt)}{ellipsis}</p>"
        if excerpt else ""
    )
    return (
        "<article class='gazette-card feed-card'>"
        f"<p class='gazette-card-date'>{escape_html(format_date(p['pubDate']))}</p>"
        f"<h3 class='gazette-card-title'>{escape_html(clean_title(p['title']).upper())}</h3>"
        f"{desc}"
        f"<a class='gazette-card-link' href='{escape_html(p['link'])}' target='_blank' rel='noopener noreferrer'>Read this edition &rarr;</a>"
        "</article>"
    )


def render_essay_card(p):
    full = strip_html(p["description"])
    excerpt = full[:ESSAY_EXCERPT_LEN]
    ellipsis = "&hellip;" if len(full) >= ESSAY_EXCERPT_LEN else ""
    desc = (
        f"<p class='sub-card-desc'>{escape_html(excerpt)}{ellipsis}</p>"
        if excerpt else ""
    )
    return (
        "<article class='sub-card feed-card'>"
        "<div class='sub-card-acc'></div>"
        f"<p class='sub-card-label'>{escape_html(format_date(p['pubDate']))}</p>"
        f"<h3 class='sub-card-title'>{escape_html(clean_title(p['title']).upper())}</h3>"
        f"{desc}"
        f"<a class='sub-card-read' href='{escape_html(p['link'])}' target='_blank' rel='noopener noreferrer'>Read the essay &rarr;</a>"
        "</article>"
    )


def replace_container_content(html_text, container_id, new_inner_html):
    """
    Replaces everything inside <div id="container_id">...</div> with
    new_inner_html, correctly handling divs nested inside (e.g. the
    sub-card-acc divs inside each essay card) by tracking tag depth
    instead of naively matching the first closing </div>.
    """
    open_tag_re = re.compile(
        r'<div\b[^>]*\bid=["\']' + re.escape(container_id) + r'["\'][^>]*>',
        re.IGNORECASE,
    )
    m = open_tag_re.search(html_text)
    if not m:
        raise ValueError(f"Could not find a container with id={container_id!r}")

    start = m.end()
    div_tag_re = re.compile(r"<div\b[^>]*>|</div>", re.IGNORECASE)
    depth = 1
    pos = start
    end = None
    while depth > 0:
        tag_match = div_tag_re.search(html_text, pos)
        if not tag_match:
            raise ValueError(f"Unbalanced <div> tags while scanning id={container_id!r}")
        if tag_match.group(0).lower().startswith("</div"):
            depth -= 1
        else:
            depth += 1
        pos = tag_match.end()
        if depth == 0:
            end = tag_match.start()

    return html_text[:start] + new_inner_html + html_text[end:]


def main():
    items = fetch_feed_items()
    if not items:
        print("No feed items returned. Leaving index.html untouched.")
        return 0

    gazette_items = sorted(
        (p for p in items if title_is_gazette(p["title"])),
        key=sort_key, reverse=True,
    )[:GAZETTE_LIMIT]

    essay_items = sorted(
        (
            p for p in items
            if not title_is_gazette(p["title"])
            and not title_looks_like_live(p["title"], p["description"])
        ),
        key=sort_key, reverse=True,
    )[:ESSAY_LIMIT]

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html_text = f.read()

    if gazette_items:
        gazette_html = "".join(render_gazette_card(p) for p in gazette_items)
        html_text = replace_container_content(html_text, "gazetteGrid", gazette_html)
    else:
        print("Warning: no Gazette items matched the title filter.")

    if essay_items:
        essay_html = "".join(render_essay_card(p) for p in essay_items)
        html_text = replace_container_content(html_text, "essayFeedGrid", essay_html)
    else:
        print("Warning: no essay items matched the title filter.")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html_text)

    print(f"Updated {len(gazette_items)} gazette card(s) and {len(essay_items)} essay card(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
