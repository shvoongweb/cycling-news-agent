# -*- coding: utf-8 -*-
"""שלב 1: איסוף ידיעות מפידי RSS וסינון לפי חלון זמן."""
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser


def _strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

from config import SOURCES, HOURS_WINDOW, MAX_RAW_ITEMS


def _entry_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def fetch_all():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    items = []
    for src in SOURCES:
        try:
            d = feedparser.parse(src["feed"], agent="Mozilla/5.0 (cycling-news-agent)")
            for e in d.entries:
                ts = _entry_time(e)
                if ts is None or ts < cutoff:
                    continue
                item = {
                    "source_name": src["name"],
                    "title": (e.get("title") or "").strip(),
                    "summary": (e.get("summary") or "")[:600],
                    "url": e.get("link") or src["site"],
                    "published": ts.isoformat(),
                }
                # לידיעות טור דה פראנס: מוסיפים טקסט מורחב (לדירוגים, חולצות וצפי)
                blob = (item["title"] + " " + item["summary"]).lower()
                if any(k in blob for k in ("tour de france", "tdf", "stage", "yellow jersey")):
                    content = ""
                    if e.get("content"):
                        content = e["content"][0].get("value", "")
                    details = _strip_html(content or e.get("summary") or "")
                    if len(details) > 200:
                        item["details"] = details[:2500]
                items.append(item)
            print(f"[fetch] {src['name']}: {len(d.entries)} בפיד")
        except Exception as ex:  # פיד בודד שנופל לא מפיל את הכל
            print(f"[fetch] שגיאה ב-{src['name']}: {ex}")

    items.sort(key=lambda x: x["published"], reverse=True)
    print(f"[fetch] סה\"כ {len(items)} ידיעות בחלון של {HOURS_WINDOW} שעות")
    return items[:MAX_RAW_ITEMS]
