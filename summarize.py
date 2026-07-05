# -*- coding: utf-8 -*-
"""שלב 2: דירוג + סיכום + תרגום לעברית עם Gemini (REST, שכבה חינמית)."""
import json
import os

import requests

from config import GEMINI_MODEL, NUM_STORIES, TDF_FOCUS

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT = """אתה עורך חדשות אופניים מקצועי הכותב בעברית לקהל ישראלי.
לפניך רשימת ידיעות (JSON) מ-30 השעות האחרונות מאתרי האופניים המובילים בעולם.

בחר את {n} הידיעות החשובות ביותר וכתוב לכל אחת:
- title_he: כותרת קצרה וקולעת בעברית (עד 12 מילים)
- paragraph_he: פסקה של 3-5 משפטים בעברית, בניסוח מקורי לחלוטין (אסור להעתיק), עם ההקשר החשוב
- image_keyword: שאילתת חיפוש תמונה באנגלית עבור הידיעה — ספציפית ככל האפשר: שם הרוכב המרכזי + ההקשר (למשל "Isaac del Toro cyclist", "Tadej Pogacar Tour de France yellow jersey"). לא מילים גנריות כמו "cycling race"

{tdf}

כללים:
- אל תמציא עובדות שאינן בידיעות המקור.
- אם כמה מקורות מסקרים אותו אירוע — אחד אותם לידיעה אחת ובחר את המקור המפורט ביותר.
- הידיעה הראשונה = החשובה ביותר.

החזר JSON בלבד, במבנה:
{{"stories": [{{"title_he": "...", "paragraph_he": "...", "image_keyword": "...", "source_name": "...", "source_url": "..."}}]}}

הידיעות:
{items}
"""

TDF_NOTE = "עכשיו מתקיים הטור דה פראנס! תן עדיפות עליונה לידיעות על הטור: תוצאות שלב, מאבקי הצמרת, נטישות, סקנדלים ותחזית לשלב הבא. ידיעה ראשונה חייבת להיות מהטור אם קיימת."


def summarize(items):
    key = os.environ["GEMINI_API_KEY"]
    prompt = PROMPT.format(
        n=NUM_STORIES,
        tdf=TDF_NOTE if TDF_FOCUS else "",
        items=json.dumps(items, ensure_ascii=False),
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    r = requests.post(API_URL.format(model=GEMINI_MODEL, key=key), json=body, timeout=120)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    stories = json.loads(text)["stories"][:NUM_STORIES]
    print(f"[gemini] התקבלו {len(stories)} ידיעות מסוכמות")
    return stories
