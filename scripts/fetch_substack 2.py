#!/usr/bin/env python3
"""Refresh a validated, last-known-good Substack cache without noisy commits."""
from __future__ import annotations

import email.utils
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

FEED = "https://ccarazas.substack.com/feed"
OUT = Path(__file__).resolve().parents[1] / "data" / "substack-posts.json"
ALLOWED_HOSTS = {"ccarazas.substack.com", "www.ccarazas.substack.com"}
MAX_POSTS = 6
OWNED_ROUTES = {
    "The Diagnosis Ceremony": "/writing/the-diagnosis-ceremony/",
    "Losing Your Identity After Loss": "/writing/losing-your-identity-after-loss/",
    "The Plymouth Sentinel & Canine Gazette": "/gazette/latest/",
}


def clean(value: str | None, limit: int = 260) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"


def valid_url(value: str | None) -> str:
    url = (value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in ALLOWED_HOSTS:
        return ""
    return url


def date_label(value: str | None) -> str:
    raw = clean(value, 100)
    if not raw:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(raw)
        return dt.strftime("%b %-d, %Y")
    except Exception:
        return raw


def item_image(node: ET.Element) -> str:
    # Substack feeds may expose images through media:content, enclosure, or HTML.
    for elem in node.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in {"content", "thumbnail", "enclosure"}:
            candidate = elem.attrib.get("url", "")
            if candidate.startswith("https://"):
                return candidate
    for key in ("description", "encoded", "content"):
        text = next((e.text or "" for e in node.iter() if e.tag.rsplit("}", 1)[-1] == key), "")
        match = re.search(r'<img[^>]+src=["\'](https://[^"\']+)', text, flags=re.I)
        if match:
            return html.unescape(match.group(1))
    return ""


def parse_feed(raw: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(raw)
    posts: list[dict[str, str]] = []
    seen: set[str] = set()

    rss_items = root.findall(".//item")
    atom_entries = [e for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "entry"]
    nodes = rss_items or atom_entries

    for node in nodes:
        def text_of(*names: str) -> str:
            for elem in node.iter():
                if elem.tag.rsplit("}", 1)[-1] in names and elem.text:
                    return elem.text
            return ""

        title = clean(text_of("title"), 120)
        link = ""
        if node.tag.rsplit("}", 1)[-1] == "entry":
            for elem in node.iter():
                if elem.tag.rsplit("}", 1)[-1] == "link":
                    candidate = elem.attrib.get("href", "")
                    if valid_url(candidate):
                        link = candidate
                        break
        else:
            link = valid_url(text_of("link"))

        if not title or not link or link in seen:
            continue
        seen.add(link)
        excerpt = clean(text_of("description", "summary", "encoded", "content"), 260)
        date = date_label(text_of("pubDate", "published", "updated"))
        post = {"title": title, "url": link, "excerpt": excerpt, "date": date}
        if title in OWNED_ROUTES:
            post["internalPath"] = OWNED_ROUTES[title]
        image = item_image(node)
        if image:
            post["image"] = image
        posts.append(post)
        if len(posts) >= MAX_POSTS:
            break
    return posts


def fetch() -> bytes:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                FEED,
                headers={
                    "User-Agent": "ChristopherCarazasSiteFeed/2.0 (+https://chriscarazas.com)",
                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(2_000_000)
                if not raw.strip().startswith(b"<"):
                    raise ValueError("Feed response was not XML")
                return raw
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Unable to fetch feed: {last_error}")


def main() -> int:
    previous: dict = {}
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            previous = {}

    try:
        posts = parse_feed(fetch())
        if not posts:
            raise ValueError("Feed returned no valid posts")

        # Do not rewrite the file just to change a timestamp. This avoids a commit every six hours.
        if posts == previous.get("posts"):
            print(f"Cache already current with {len(posts)} posts")
            return 0

        payload = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": FEED,
            "posts": posts,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=OUT.parent, delete=False) as temp:
            temp.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            temp_path = Path(temp.name)
        temp_path.replace(OUT)
        print(f"Wrote {len(posts)} validated posts")
        return 0
    except Exception as exc:
        print(f"Feed refresh failed; preserving last-known-good cache: {exc}", file=sys.stderr)
        return 0 if previous.get("posts") else 1


if __name__ == "__main__":
    raise SystemExit(main())
