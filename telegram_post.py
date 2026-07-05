# -*- coding: utf-8 -*-
"""שלב 4: שליחה לטלגרם — מקבץ הידיעות + קישור לכתבה + קובץ HTML לפתיחה בדפדפן."""
import html
import os

import requests

from config import BRAND_TITLE

API = "https://api.telegram.org/bot{token}/{method}"


def _esc(s):
    return html.escape(s or "")


def _block(i, s):
    return (
        f"<b>{i}. {_esc(s['title_he'])}</b>\n"
        f"{_esc(s['paragraph_he'])}\n"
        f'🔗 <a href="{_esc(s["source_url"])}">{_esc(s["source_name"])}</a>'
    )


def _pages_url():
    """כתובת GitHub Pages נגזרת אוטומטית משם ה-repo שבו רץ ה-Action."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")  # owner/repo
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}/"
    return ""


def _send_photo(token, chat_id, image_bytes, file_name, caption):
    r = requests.post(
        API.format(token=token, method="sendPhoto"),
        data={"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"},
        files={"photo": (file_name or "image.jpg", image_bytes, "image/jpeg")},
        timeout=60,
    )
    r.raise_for_status()


def post_to_telegram(stories, date_str, html_path, image_bytes=None,
                     image_name=None, image_credit=""):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    rest = stories
    if image_bytes:
        # תמונה ראשית + כיתוב: כותרת + הידיעה המובילה
        caption = f"<b>🚴‍♂️ {BRAND_TITLE} — {date_str}</b>\n\n" + _block(1, stories[0])
        if image_credit:
            caption += f"\n<i>{_esc(image_credit)}</i>"
        _send_photo(token, chat_id, image_bytes, image_name, caption)
        print("[telegram] נשלחה תמונה ראשית")
        rest = stories[1:]
        parts = []
        start = 2
    else:
        parts = [f"<b>🚴‍♂️ {BRAND_TITLE} — {date_str}</b>", ""]
        start = 1

    for i, s in enumerate(rest, start):
        parts.append(_block(i, s))
        parts.append("")
    url = _pages_url()
    if url:
        parts.append(f'📰 <a href="{url}">לצפייה בכתבה המלאה בדפדפן</a>')
    text = "\n".join(parts).strip()

    # טלגרם מגביל הודעה ל-4096 תווים — חוצים לשתיים אם צריך
    chunks = []
    while text:
        chunks.append(text[:4000])
        text = text[4000:]
    for chunk in chunks:
        r = requests.post(
            API.format(token=token, method="sendMessage"),
            json={"chat_id": chat_id, "text": chunk, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=30,
        )
        r.raise_for_status()
    print("[telegram] נשלח מקבץ הידיעות")

    # קובץ ה-HTML כמסמך — פתיחה בדפדפן בלחיצה, גם בלי אינטרנט לדף
    with open(html_path, "rb") as f:
        r = requests.post(
            API.format(token=token, method="sendDocument"),
            data={"chat_id": chat_id, "caption": f"📄 {BRAND_TITLE} — {date_str} (לפתיחה בדפדפן)"},
            files={"document": (os.path.basename(html_path), f, "text/html")},
            timeout=60,
        )
        r.raise_for_status()
    print("[telegram] נשלח קובץ ה-HTML")
