# -*- coding: utf-8 -*-
"""שליפת דירוגים רשמיים מהאתר הרשמי של הטור דה פראנס (letour.fr).
מחזיר טקסט דירוגים עדכני: דירוג כללי (5 מובילים) + מובילי 4 החולצות,
כמקור סמכות עבור Gemini. מחזיר None אם השליפה נכשלה."""
import re

import requests

BASE = "https://www.letour.fr"
RANKINGS = BASE + "/en/rankings"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# סוג-סיווג באתר → תווית עברית (חולצה). הסדר קובע את סדר ההצגה.
TYPES = [
    ("ite", "דירוג כללי (חולצה צהובה)"),
    ("ipe", "נקודות (חולצה ירוקה)"),
    ("ime", "מלך ההרים (חולצה מנוקדת)"),
    ("ije", "רוכב צעיר (חולצה לבנה)"),
]


def _to_text(html):
    t = re.sub(r"<[^>]+>", " ", html)
    t = (t.replace("&nbsp;", " ").replace("&#039;", "'")
          .replace("&#39;", "'").replace("&amp;", "&"))
    return re.sub(r"\s+", " ", t).strip()


def fetch_standings():
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        main = s.get(RANKINGS, timeout=30)
        main.raise_for_status()
        html = main.text

        m = re.search(r"STAGE\s*(\d+)", html, re.I)
        stage = m.group(1) if m else ""

        ajax = {}
        for url, typ in re.findall(
            r'data-tabs-ajax="([^"]+)"\s+data-type="([^"]+)"', html
        ):
            ajax.setdefault(typ, url)

        blocks = []
        for typ, label in TYPES:
            url = ajax.get(typ)
            if not url:
                continue
            r = s.get(BASE + url,
                      headers={"X-Requested-With": "XMLHttpRequest"}, timeout=30)
            if not r.ok:
                continue
            txt = _to_text(r.text)
            i = txt.find("Rank Rider")
            # קטע ארוך דיו כדי לכלול את עמודת הזמן/פער של 5 המקומות הראשונים
            snippet = txt[i:i + 850] if i >= 0 else txt[:850]
            blocks.append(f"### {label}\n{snippet}")

        if not blocks:
            print("[standings] letour: לא נמצאו טבלאות דירוג")
            return None

        header = (f"דירוג רשמי מ-letour.fr — לאחר שלב {stage}" if stage
                  else "דירוג רשמי מ-letour.fr")
        blob = header + "\n\n" + "\n\n".join(blocks)
        print(f"[standings] letour: נשלפו {len(blocks)} סיווגים (שלב {stage})")
        return blob[:4500]
    except Exception as ex:
        print(f"[standings] letour שגיאה: {ex}")
        return None
