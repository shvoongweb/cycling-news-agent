# -*- coding: utf-8 -*-
"""חיפוש תמונה: קודם ויקישיתוף (תמונות אמיתיות של הרוכבים, רישיון חופשי),
ואז Pexels כגיבוי (סטוק מרוץ כביש)."""
import os
import random
import re

import requests

UA = {"User-Agent": "cycling-news-agent/1.0 (daily Hebrew cycling digest)"}


def _clean_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def from_source(img_url, source_name):
    """תמונת הקטע מהכתבה עצמה (צילום אמיתי מהיום) — עדיפה על סטוק גנרי."""
    if not img_url:
        return None, None, None, None
    try:
        base = img_url.split("?")[0].lower()
        ext = next((e for e in (".jpg", ".jpeg", ".png", ".webp") if base.endswith(e)), "")
        r = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0 (cycling-news-agent)"}, timeout=30)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "").lower()
        if "image" not in ctype and not ext:
            print(f"[image] תמונת מקור אינה תמונה ({ctype or 'ללא סוג'})")
            return None, None, None, None
        if len(r.content) < 12000:  # תמונות זעירות/placeholder — לא ראויות לירו
            print("[image] תמונת מקור קטנה מדי — מדלגים")
            return None, None, None, None
        fmt = ext.lstrip(".") or ("png" if "png" in ctype else "webp" if "webp" in ctype else "jpg")
        credit = f"צילום: {source_name}" if source_name else "צילום מהכתבה במקור"
        print(f"[image] נעשה שימוש בתמונת הקטע מהמקור ({source_name})")
        return r.content, f"stage-photo.{fmt}", credit, img_url
    except Exception as e:
        print(f"[image] תמונת מקור נכשלה: {e}")
        return None, None, None, None


def _wikimedia(query):
    """תמונה חופשית אמיתית מוויקישיתוף לפי שם רוכב/אירוע."""
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6, "gsrlimit": 20,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size",
                "iiurlwidth": 1280,
            },
            headers=UA, timeout=20,
        )
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
        candidates = []
        for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
            info = (p.get("imageinfo") or [{}])[0]
            w, h = info.get("width", 0), info.get("height", 0)
            if w < 640 or h < 360 or h > w * 1.2:  # מעדיפים תמונה רוחבית סבירה
                continue
            candidates.append(info)
        if not candidates:
            print(f"[image] ויקישיתוף: אין תוצאה מתאימה ל-'{query}'")
            return None, None, None, None
        # בחירה אקראית מתוך המועמדות המובילות — כדי שלא תחזור אותה תמונה כל יום
        best = random.choice(candidates[:8])

        meta = best.get("extmetadata") or {}
        artist = _clean_html((meta.get("Artist") or {}).get("value", ""))[:60]
        lic = _clean_html((meta.get("LicenseShortName") or {}).get("value", ""))
        credit = f"צילום: {artist or 'Wikimedia Commons'} ({lic or 'Wikimedia Commons'})"
        img_url = best.get("thumburl") or best.get("url")

        img = requests.get(img_url, headers=UA, timeout=30)
        img.raise_for_status()
        print(f"[image] ויקישיתוף: נמצאה תמונה ל-'{query}' ({credit})")
        return img.content, "cycling-news.jpg", credit, img_url
    except Exception as e:
        print(f"[image] ויקישיתוף נכשל: {e}")
        return None, None, None, None


def _pexels(query):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        print("[image] חסר PEXELS_API_KEY")
        return None, None, None, None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            timeout=20,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            print(f"[image] Pexels: לא נמצאה תמונה ל-'{query}'")
            return None, None, None, None
        photo = random.choice(photos)  # גיוון — לא תמיד התוצאה הראשונה
        img_url = photo["src"].get("large2x") or photo["src"]["large"]
        credit = f'צילום: {photo.get("photographer", "Pexels")} / Pexels'
        img = requests.get(img_url, timeout=30)
        img.raise_for_status()
        print(f"[image] Pexels: נמצאה תמונה ל-'{query}' ({credit})")
        return img.content, f"cycling-news-{photo['id']}.jpg", credit, img_url
    except Exception as e:
        print(f"[image] Pexels נכשל: {e}")
        return None, None, None, None


def find_image(query):
    """מחזיר (image_bytes, file_name, credit, image_url) או (None,)*4."""
    words = query.split()
    # ניסיונות בוויקישיתוף: מהשאילתה המלאה ועד שם הרוכב בלבד
    attempts = [query]
    if len(words) > 4:
        attempts.append(" ".join(words[:4]))
    if len(words) > 3:
        attempts.append(" ".join(words[:3]))  # לרוב שם הרוכב המלא
    attempts.append(" ".join(words[:3]) + " cyclist")
    attempts.append("Tour de France peloton")

    seen = set()
    for q in attempts:
        if q.lower() in seen:
            continue
        seen.add(q.lower())
        result = _wikimedia(q)
        if result[0]:
            return result

    # גיבוי אחרון: Pexels עם שאילתה מתחלפת
    fallback = random.choice([
        "road cycling race peloton",
        "professional cycling race",
        "cyclists climbing mountain road race",
        "cycling sprint finish race",
        "peloton france cycling",
    ])
    return _pexels(fallback)
