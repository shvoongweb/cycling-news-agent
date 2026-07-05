# -*- coding: utf-8 -*-
"""שלב 2: Gemini — מיני-כתבת טור דה פראנס + ידיעות קצרות, בעברית."""
import json
import os

import requests

from config import GEMINI_MODEL, NUM_STORIES, TDF_FOCUS

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT_TDF = """אתה עורך חדשות אופניים מקצועי הכותב בעברית לקהל ישראלי.
לפניך רשימת ידיעות (JSON) מ-30 השעות האחרונות מאתרי האופניים המובילים בעולם. חלק מהידיעות כוללות שדה details עם טקסט מורחב.

צור JSON עם שני חלקים:

1. "tdf_feature" — מיני-כתבה על הטור דה פראנס של היום:
   - "title_he": כותרת ראשית קולעת (עד 12 מילים)
   - "recap_he": 2-3 פסקאות (מופרדות ב-\\n\\n) על מה שקרה היום בשלב: מי ניצח, איך התפתח המרוץ, דרמות ורגעים חשובים
   - "top5_he": מערך של עד 5 מחרוזות — הדירוג הכללי המעודכן: "שם הרוכב (קבוצה) — פער". אך ורק אם הנתונים מופיעים במפורש בידיעות! אם אין — מערך ריק []
   - "jerseys_he": מערך מחרוזות של לובשי החולצות: "🟡 צהובה: שם", "🟢 ירוקה: שם", "🔴 מנוקדת: שם", "⚪ לבנה: שם". רק חולצות שידוע מי לובש אותן לפי הידיעות. אם אין מידע — []
   - "next_stage_he": פסקה על השלב הבא (מסלול, אופי, למי מתאים) אם יש מידע בידיעות, אחרת ""
   - "image_keyword": שאילתת תמונה באנגלית — שם הרוכב המרכזי + הקשר (למשל "Isaac del Toro cyclist")
   - "source_name", "source_url": המקור העיקרי

2. "stories" — {n} ידיעות קצרות על נושאים אחרים (לא מה שכבר סוקר בכתבה הראשית):
   לכל אחת: "title_he" (כותרת קצרה), "paragraph_he" (פסקה של 3-4 משפטים בניסוח מקורי), "source_name", "source_url"

כללים מחייבים:
- אסור להמציא עובדות, שמות, זמנים או פערים שלא מופיעים בידיעות המקור. עדיף סעיף ריק מנתון מומצא.
- ניסוח מקורי לחלוטין — לא תרגום מילולי.
- אם אין בכלל ידיעות על הטור דה פראנס: "tdf_feature": null, ו-"stories" יכיל {n_alt} ידיעות.

החזר JSON בלבד:
{{"tdf_feature": {{...}} או null, "stories": [...]}}

הידיעות:
{items}
"""

PROMPT_REGULAR = """אתה עורך חדשות אופניים מקצועי הכותב בעברית לקהל ישראלי.
לפניך רשימת ידיעות (JSON). בחר את {n_alt} החשובות וכתוב לכל אחת title_he, paragraph_he (3-5 משפטים, ניסוח מקורי), image_keyword (שם רוכב/אירוע באנגלית), source_name, source_url.
אסור להמציא עובדות. החזר JSON בלבד: {{"tdf_feature": null, "stories": [...]}}

הידיעות:
{items}
"""


def summarize(items):
    key = os.environ["GEMINI_API_KEY"]
    template = PROMPT_TDF if TDF_FOCUS else PROMPT_REGULAR
    prompt = template.format(
        n=NUM_STORIES - 1, n_alt=NUM_STORIES,
        items=json.dumps(items, ensure_ascii=False),
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    r = requests.post(API_URL.format(model=GEMINI_MODEL, key=key), json=body, timeout=180)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    data = json.loads(text)
    feature = data.get("tdf_feature")
    stories = data.get("stories") or []
    print(f"[gemini] כתבה ראשית: {'כן' if feature else 'אין'} | ידיעות קצרות: {len(stories)}")
    return feature, stories
