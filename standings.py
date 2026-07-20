# -*- coding: utf-8 -*-
"""שליפת דירוגים רשמיים מהאתר הרשמי של הטור דה פראנס (letour.fr).

מחזיר טקסט דירוגים עדכני כמקור סמכות עבור Gemini:
  * דירוג כללי מצטבר (GC) + שלושת סיווגי החולצות הנוספים - מלשונית "General ranking"
  * תוצאות הקטע האחרון - מלשונית "Stage ranking"
  * לובשי החולצות בפועל, מחושבים לפי הכלל שרוכב לובש חולצה אחת בלבד

חשוב: הדף /en/rankings נטען כברירת מחדל על לשונית "Stage ranking", ולכן
כתובות ה-AJAX שמופיעות ב-data-tabs-ajax הן של הקטע הבודד (סיומת e = etape)
ולא של הדירוג המצטבר (סיומת g = general). לכן שולפים את הכתובות הנכונות
מתוך data-ajax-stack, שם מופיעים המפתחות itg/ipg/img/ijg.

מחזיר None אם השליפה נכשלה.
"""
import re

import requests

BASE = "https://www.letour.fr"
RANKINGS = BASE + "/en/rankings"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# מפתח AJAX -> תווית עברית. הסדר קובע את סדר ההצגה ואת סדר החולצות.
GENERAL = [
    ("itg", "דירוג כללי (חולצה צהובה)"),
    ("ipg", "נקודות (חולצה ירוקה)"),
    ("img", "מלך ההרים (חולצה מנוקדת)"),
    ("ijg", "רוכב צעיר (חולצה לבנה)"),
]
JERSEY_LABELS = ["🟡 צהובה (מוביל כללי)", "🟢 ירוקה (נקודות)",
                 "🔴 מנוקדת (מלך ההרים)", "⚪ לבנה (רוכב צעיר)"]
STAGE_KEY = "ite"  # דירוג הקטע האחרון (individual / etape)

AJAX_RE = re.compile(
    r'"(itg|ipg|img|ijg|ite)"\s*:\s*'
    r'"(/en/ajax/ranking/\d+/[a-z]{3}/[a-f0-9]+/[a-z]+)"')
TD_RE = re.compile(r'<td class="([^"]*)"[^>]*>(.*?)</td>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
HOURS_RE = re.compile(r"(\d+)\s*h")


def _to_text(html):
    t = TAG_RE.sub(" ", html)
    t = (t.replace("&nbsp;", " ").replace("&#039;", "'")
          .replace("&#39;", "'").replace("&amp;", "&").replace("&quot;", '"'))
    return re.sub(r"\s+", " ", t).strip()


def _parse_rows(html):
    """מפרק טבלת דירוג ל-[{name, team, value, gap}]. עמיד לשינויי עמודות:
    שם הרוכב והקבוצה מזוהים לפי class, והערכים הם התאים שאחרי הקבוצה."""
    rows = []
    for chunk in re.split(r"<tr[\s>]", html)[1:]:
        cells = [(cls, _to_text(inner)) for cls, inner in TD_RE.findall(chunk)]
        name = team = ""
        team_idx = -1
        for i, (cls, txt) in enumerate(cells):
            if "profile runner" in cls and not name:
                name = txt
            elif re.search(r"\bteam\b", cls) and not team:
                team, team_idx = txt, i
        if not name:
            continue
        rest = [t for _, t in cells[team_idx + 1:]] if team_idx >= 0 else []
        rows.append({
            "name": name,
            "team": team,
            "value": rest[0] if rest else "",
            "gap": rest[1] if len(rest) > 1 else "",
        })
    return rows


def _format(rows, limit=5):
    out = []
    for i, r in enumerate(rows[:limit], 1):
        line = f"{i}. {r['name']}"
        if r["team"]:
            line += f" ({r['team']})"
        if r["value"]:
            line += f" - {r['value']}"
        if r["gap"] and r["gap"] != "-":
            line += f" | פער: {r['gap']}"
        out.append(line)
    return "\n".join(out)


def _jersey_wearers(tables):
    """לובשי החולצות בפועל: רוכב לובש חולצה אחת בלבד, ולכן אם מוביל סיווג
    כבר לובש חולצה בכירה יותר - החולצה עוברת לרוכב הבא בסיווג."""
    taken, wearers = set(), []
    for key, _ in GENERAL:
        pick = ""
        for r in tables.get(key, []):
            if r["name"] and r["name"] not in taken:
                pick = r["name"]
                taken.add(pick)
                break
        wearers.append(pick or "טרם עודכן")
    return wearers


def _sanity_check(tables, stage):
    """שומר מפני רגרסיה שבה נשלפת שוב טבלת הקטע במקום הדירוג המצטבר."""
    gc, st = tables.get("itg") or [], tables.get(STAGE_KEY) or []
    if not gc:
        return
    lead = gc[0].get("value", "")
    hours = HOURS_RE.search(lead)
    try:
        stage_no = int(stage)
    except (TypeError, ValueError):
        stage_no = 0
    if stage_no >= 5 and hours and int(hours.group(1)) < 10:
        print(f"[standings] אזהרה: זמן המוביל בכללי ({lead}) נראה כזמן קטע "
              f"ולא כזמן מצטבר אחרי שלב {stage_no}")
    if st and stage_no > 1:
        same = [(r["name"], r["value"]) for r in gc[:5]] == \
               [(r["name"], r["value"]) for r in st[:5]]
        if same:
            print("[standings] אזהרה: הדירוג הכללי זהה לתוצאות הקטע - "
                  "ייתכן ששתי הטבלאות נשלפו מאותו מקור")


def fetch_standings():
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        main = s.get(RANKINGS, timeout=30)
        main.raise_for_status()

        # data-ajax-stack מגיע כ-JSON מקודד בתוך אטריביוט
        norm = main.text.replace("\\/", "/").replace("&quot;", '"')
        m = re.search(r"STAGE\s*(\d+)", norm, re.I)
        stage = m.group(1) if m else ""

        urls = {}
        for key, url in AJAX_RE.findall(norm):
            urls.setdefault(key, url)

        missing = [k for k, _ in GENERAL if k not in urls]
        if missing:
            print(f"[standings] letour: חסרות כתובות לדירוג המצטבר {missing}")

        tables = {}
        for key in [k for k, _ in GENERAL] + [STAGE_KEY]:
            url = urls.get(key)
            if not url:
                continue
            r = s.get(BASE + url,
                      headers={"X-Requested-With": "XMLHttpRequest"}, timeout=30)
            if not r.ok:
                print(f"[standings] letour: {key} החזיר {r.status_code}")
                continue
            rows = _parse_rows(r.text)
            if rows:
                tables[key] = rows

        if not tables.get("itg"):
            print("[standings] letour: לא נמצא דירוג כללי מצטבר")
            return None

        _sanity_check(tables, stage)

        blocks = []
        for key, label in GENERAL:
            if key in tables:
                blocks.append(f"### {label}\n{_format(tables[key])}")

        wearers = _jersey_wearers(tables)
        blocks.append("### לובשי החולצות בפועל (השתמש בשמות אלו ל-jerseys_he)\n"
                      + "\n".join(f"{lab}: {name}"
                                  for lab, name in zip(JERSEY_LABELS, wearers)))

        if STAGE_KEY in tables:
            blocks.append("### תוצאות הקטע האחרון בלבד "
                          "(זמני הקטע - זה איננו הדירוג הכללי!)\n"
                          + _format(tables[STAGE_KEY]))

        header = (f"דירוג רשמי מ-letour.fr - לאחר שלב {stage}" if stage
                  else "דירוג רשמי מ-letour.fr")
        blob = header + "\n\n" + "\n\n".join(blocks)
        print(f"[standings] letour: נשלפו {len(tables)} טבלאות (שלב {stage}) | "
              f"צהובה: {wearers[0]}")
        return blob[:4500]
    except Exception as ex:
        print(f"[standings] letour שגיאה: {ex}")
        return None
