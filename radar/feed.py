"""RSS/Atom helpers shared by the feed-based sources."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = _TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    # RFC 822 (RSS)
    try:
        dt = parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    # ISO 8601 (Atom / JSON)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(xml_text: str) -> list[dict]:
    """Parse RSS 2.0 or Atom into a list of {title, link, published, summary, source}."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items: list[dict] = []
    for node in root.iter():
        name = _localname(node.tag)
        if name not in ("item", "entry"):
            continue

        fields: dict[str, str] = {}
        link = ""
        for child in node:
            cname = _localname(child.tag)
            if cname == "link":
                link = (child.text or "").strip() or child.attrib.get("href", "")
            elif cname in ("title", "summary", "description", "published", "updated", "pubDate"):
                fields.setdefault(cname, (child.text or "").strip())

        published = (
            fields.get("pubDate")
            or fields.get("published")
            or fields.get("updated")
        )
        items.append(
            {
                "title": strip_html(fields.get("title", "")),
                "link": link,
                "published": parse_date(published),
                "summary": strip_html(fields.get("summary") or fields.get("description") or ""),
            }
        )
    return items
