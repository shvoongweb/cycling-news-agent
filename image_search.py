# -*- coding: utf-8 -*-
"""חיפוש תמונה חופשית מ-Pexels (מותר לשימוש מסחרי, עם קרדיט)."""
import os

import requests


def find_image(query):
    """מחזיר (image_bytes, file_name, credit, image_url) או (None,)*4 אם לא נמצא."""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        print("[image] חסר PEXELS_API_KEY — ממשיכים בלי תמונה")
        return None, None, None, None

    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            timeout=20,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            print(f"[image] לא נמצאה תמונה ל-'{query}'")
            return None, None, None, None

        photo = photos[0]
        img_url = photo["src"].get("large2x") or photo["src"]["large"]
        credit = f'צילום: {photo.get("photographer", "Pexels")} / Pexels'

        img = requests.get(img_url, timeout=30)
        img.raise_for_status()
        file_name = f"cycling-news-{photo['id']}.jpg"
        print(f"[image] נמצאה תמונה ל-'{query}' ({credit})")
        return img.content, file_name, credit, img_url
    except Exception as e:
        print(f"[image] שגיאה בחיפוש תמונה: {e}")
        return None, None, None, None
