# -*- coding: utf-8 -*-
"""תזמור הצינור: איסוף ← Gemini ← HTML ← טלגרם."""
import sys

from fetch_news import fetch_all
from summarize import summarize
from image_search import find_image
from build_html import build_html
from telegram_post import post_to_telegram


def main():
    items = fetch_all()
    if not items:
        print("[main] אין ידיעות בחלון הזמן — מסיימים בלי לפרסם")
        return

    stories = summarize(items)
    if not stories:
        print("[main] Gemini לא החזיר ידיעות — מסיימים")
        sys.exit(1)

    keyword = stories[0].get("image_keyword") or "tour de france cycling"
    img_bytes, img_name, img_credit, img_url = find_image(keyword)

    html_path, date_str = build_html(stories, img_url, img_credit or "")

    try:
        post_to_telegram(stories, date_str, html_path, img_bytes, img_name, img_credit or "")
    except Exception as ex:
        print(f"[main] שליחת טלגרם נכשלה: {ex}")
        sys.exit(1)

    print("[main] הצינור הסתיים בהצלחה ✓")


if __name__ == "__main__":
    main()
