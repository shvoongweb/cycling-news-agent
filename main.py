# -*- coding: utf-8 -*-
"""תזמור הצינור: איסוף ← דירוגים רשמיים ← Gemini ← HTML ← טלגרם."""
import sys

from fetch_news import fetch_all
from standings import fetch_standings
from summarize import summarize
from image_search import find_image, from_source
from build_html import build_html
from telegram_post import post_to_telegram
from config import TDF_FOCUS


def main():
    items = fetch_all()
    if not items:
        print("[main] אין ידיעות בחלון הזמן — מסיימים בלי לפרסם")
        return

    standings = fetch_standings() if TDF_FOCUS else None
    feature, stories = summarize(items, standings)
    if not feature and not stories:
        print("[main] Gemini לא החזיר תוכן — מסיימים")
        sys.exit(1)

    # תמונה: עדיפות עליונה לצילום הקטע מהכתבה במקור (אמיתי, מהיום),
    # ורק אם אין — נופלים לחיפוש תמונה חופשית לפי מילת מפתח.
    by_url = {it["url"]: it for it in items if it.get("url")}
    src_url = ((feature or {}).get("source_url")
               or (stories[0].get("source_url") if stories else ""))
    src_name = ((feature or {}).get("source_name")
                or (stories[0].get("source_name") if stories else ""))
    src_item = by_url.get(src_url)

    img_bytes = img_name = img_credit = img_url = None
    if src_item and src_item.get("image"):
        img_bytes, img_name, img_credit, img_url = from_source(src_item["image"], src_name)

    if not img_bytes:
        keyword = ((feature or {}).get("image_keyword")
                   or (stories[0].get("image_keyword") if stories else "")
                   or "tour de france cycling")
        img_bytes, img_name, img_credit, img_url = find_image(keyword)

    html_path, date_str = build_html(feature, stories, img_url, img_credit or "")

    try:
        post_to_telegram(feature, stories, date_str, html_path,
                         img_bytes, img_name, img_credit or "")
    except Exception as ex:
        print(f"[main] שליחת טלגרם נכשלה: {ex}")
        sys.exit(1)

    print("[main] הצינור הסתיים בהצלחה ✓")


if __name__ == "__main__":
    main()
