# -*- coding: utf-8 -*-
"""שלב 2: Gemini — מיני-כתבת טור דה פראנס + ידיעות קצרות, בעברית."""
import json
import os
import time

import requests

from config import GEMINI_MODEL, NUM_STORIES, TDF_FOCUS

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT_TDF = """אתה עורך חדשות אופניים מקצועי הכותב בעברית לקהל ישראלי.
לפניך רשימת ידיעות (JSON) מ-30 השעות האחרונות מאתרי האופניים המובילים בעולם. חלק מהידיעות כוללות שדה details עם טקסט מורחב.
ייתכן שבסוף ההנחיה מצורף בלוק "דירוג רשמי מ-letour.fr" — זהו מקור הסמכות הרשמי של הטור, והוא גובר על כל מספר אחר.

צור JSON עם שני חלקים:

1. "tdf_feature" — מיני-כתבה על הטור דה פראנס של היום. הסדר קבוע: פתיח → מתכוננים לקטע הבא → חמשת הראשונים בקטע → דירוג כללי → חולצות. מלא את כל השדות:
   - "title_he": כותרת ראשית קולעת (עד 12 מילים)
   - "recap_he": 2-3 פסקאות (מופרדות ב-\\n\\n) על מה שקרה היום בקטע: מי ניצח, איך התפתח המרוץ, דרמות ורגעים חשובים
   - "next_stage_he": פסקה על הקטע הבא — מסלול, אופי (שטוח/הרים/פרט), ולמי הוא מתאים — אם יש מידע בידיעות, אחרת ""
   - "stage_top5_he": מערך של עד 5 מחרוזות — חמשת הראשונים בקטע של היום עצמו (תוצאת הקטע, לא הדירוג הכללי!). כל פריט **חייב לכלול זמן**: המנצח בפורמט "שם הרוכב (קבוצה) — זמן הקטע" (למשל "4:23:11"), והשאר לפי הפרש מהמנצח "שם הרוכב (קבוצה) — +ש:שנ" (למשל "+0:04"; מי שסיים באותו זמן — "+0:00" או "אותו זמן"). קח את הזמנים מדיווח המרוץ בידיעות המקור. אם באמת אין נתוני זמן בשום ידיעה — מערך ריק [] (אל תמציא ואל תחזיר שמות בלי זמן)
   - "top5_he": מערך של 5 מחרוזות בדיוק — חמשת המובילים בדירוג הכללי (GC) לאחר הקטע. כל פריט **חייב לכלול זמן/פער**: המוביל בפורמט "שם הרוכב (קבוצה) — מוביל" והשאר "שם הרוכב (קבוצה) — +ד:שנ" (למשל "+0:45"). קח אותם מהבלוק "דירוג רשמי מ-letour.fr" תחת "דירוג כללי (חולצה צהובה)" — שם מופיעה עמודת הזמן/פער; העתק אותה במדויק. אם אין דירוג רשמי מצורף — קח את הפערים מהמפורש בידיעות. אם אין נתוני זמן כלל — מערך ריק []
   - "jerseys_he": מערך של בדיוק 4 מחרוזות — לובשי החולצות לאחר הקטע לפי הסדר: "🟡 צהובה (מוביל כללי): שם", "🟢 ירוקה (נקודות): שם", "🔴 מנוקדת (מלך ההרים): שם", "⚪ לבנה (רוכב צעיר): שם". קח את שם הרוכב במקום ה-1 בכל סיווג מהבלוק "דירוג רשמי מ-letour.fr" (צהובה=דירוג כללי, ירוקה=נקודות, מנוקדת=מלך ההרים, לבנה=רוכב צעיר). אם הדירוג הרשמי חסר, נסה מהידיעות; חולצה שאין עליה מידע — כתוב "טרם עודכן". תמיד 4 פריטים בדיוק, ולעולם אל תמציא שם
   - "image_keyword": שאילתת תמונה באנגלית — שם הרוכב המרכזי + הקשר (למשל "Isaac del Toro cyclist")
   - "source_name", "source_url": המקור העיקרי

2. "stories" — {n} ידיעות קצרות על נושאים אחרים (לא מה שכבר סוקר בכתבה הראשית):
   לכל אחת: "title_he" (כותרת קצרה), "paragraph_he" (פסקה של 3-4 משפטים בניסוח מקורי), "source_name", "source_url"

כללים מחייבים:
- שמות רוכבים תמיד בעברית מלאה (שם פרטי + משפחה) כשידוע לך; אחרת תעתיק את שם המשפחה.
- אסור להמציא עובדות, שמות, זמנים או פערים שלא מופיעים בידיעות המקור או בדירוג הרשמי. עדיף "טרם עודכן" מנתון מומצא.
- ניסוח מקורי לחלוטין — לא תרגום מילולי.
- אם אין בכלל ידיעות על הטור דה פראנס: "tdf_feature": null, ו-"stories" יכיל {n_alt} ידיעות.

החזר JSON תקין בלבד (ללא טקסט נוסף וללא סימוני קוד):
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


def _clean_json(text):
    """חילוץ JSON תקין גם אם המודל עטף בטקסט/סימוני קוד."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _ask_gemini(prompt, key):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    r = requests.post(API_URL.format(model=GEMINI_MODEL, key=key), json=body, timeout=180)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _clean_json(text)


def summarize(items, standings=None):
    key = os.environ["GEMINI_API_KEY"]
    template = PROMPT_TDF if TDF_FOCUS else PROMPT_REGULAR
    # שדה image הוא לשימוש פנימי (תמונת הירו) — לא נשלח למודל
    payload = [{k: v for k, v in it.items() if k != "image"} for it in items]
    prompt = template.format(
        n=NUM_STORIES - 1, n_alt=NUM_STORIES,
        items=json.dumps(payload, ensure_ascii=False),
    )
    if standings:
        prompt += ("\n\n--- דירוג רשמי מ-letour.fr (מקור סמכות — השתמש בו לפני הכל "
                   "עבור top5_he ו-jerseys_he) ---\n" + standings)

    data = None
    last_err = None
    for attempt in range(1, 4):
        try:
            data = _ask_gemini(prompt, key)
            break
        except (requests.RequestException, json.JSONDecodeError, KeyError) as ex:
            last_err = ex
            print(f"[gemini] ניסיון {attempt}/3 נכשל: {ex}")
            time.sleep(4)
    if data is None:
        raise last_err

    feature = data.get("tdf_feature")
    stories = data.get("stories") or []
    print(f"[gemini] כתבה ראשית: {'כן' if feature else 'אין'} | ידיעות קצרות: {len(stories)}")
    return feature, stories
