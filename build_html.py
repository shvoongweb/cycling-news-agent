# -*- coding: utf-8 -*-
"""שלב 3: בניית כתבת HTML יומית (עברית, RTL) לתיקיית docs/ עבור GitHub Pages."""
import html
import os
from datetime import datetime, timezone, timedelta

from config import BRAND_TITLE

DOCS_DIR = "docs"

CSS = """
body{font-family:'Segoe UI',Arial,sans-serif;direction:rtl;background:#f5f6fa;margin:0;color:#1a1a2e}
.wrap{max-width:760px;margin:0 auto;padding:24px 16px}
header{background:linear-gradient(135deg,#ffd200,#1a1a2e);border-radius:14px;padding:28px 24px;color:#fff;text-align:center}
header h1{margin:0;font-size:1.9em}header .date{opacity:.85;margin-top:6px}
article{background:#fff;border-radius:12px;padding:20px 22px;margin-top:16px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
article h2{margin:0 0 10px;font-size:1.25em;color:#16213e}
article p{line-height:1.7;margin:0 0 12px}
.src a{color:#0f3460;font-weight:600;text-decoration:none}
.lead{border-right:5px solid #ffd200}
.feature h2{font-size:1.5em}
.feature h3{font-size:1.05em;color:#0f3460;margin:18px 0 8px;border-bottom:2px solid #ffd200;padding-bottom:4px;display:inline-block}
.feature ul{margin:0;padding-right:20px;line-height:1.9}
.brief-title{font-size:1.2em;color:#16213e;margin:24px 0 0;text-align:center}
footer{text-align:center;color:#888;font-size:.85em;padding:20px 0}
nav.arch{text-align:center;margin-top:10px}nav.arch a{color:#0f3460;margin:0 8px}
"""


def _esc(s):
    return html.escape(s or "")


def _feature_block(f):
    """מיני-כתבת הטור דה פראנס."""
    if not f:
        return ""
    parts = [f'<article class="lead feature"><h2>{_esc(f["title_he"])}</h2>']
    for para in (f.get("recap_he") or "").split("\n\n"):
        if para.strip():
            parts.append(f"<p>{_esc(para.strip())}</p>")
    if f.get("top5_he"):
        parts.append("<h3>🏆 הדירוג הכללי</h3><ul>")
        parts.extend(f"<li>{_esc(x)}</li>" for x in f["top5_he"][:5])
        parts.append("</ul>")
    if f.get("jerseys_he"):
        parts.append("<h3>👕 לובשי החולצות</h3><ul>")
        parts.extend(f"<li>{_esc(x)}</li>" for x in f["jerseys_he"])
        parts.append("</ul>")
    if (f.get("next_stage_he") or "").strip():
        parts.append(f'<h3>🔮 מבט לשלב הבא</h3><p>{_esc(f["next_stage_he"].strip())}</p>')
    parts.append(
        f'<p class="src">🔗 <a href="{_esc(f["source_url"])}" target="_blank" rel="noopener">{_esc(f["source_name"])}</a></p></article>'
    )
    return "".join(parts)


def build_page(feature, stories, date_str, image_url=None, image_credit=""):
    blocks = [_feature_block(feature)]
    if feature and stories:
        blocks.append('<h2 class="brief-title">⚡ ובשאר עולם האופניים</h2>')
    for i, s in enumerate(stories, 1):
        cls = "lead" if (not feature and i == 1) else ""
        blocks.append(
            f'<article class="{cls}"><h2>{i}. {_esc(s["title_he"])}</h2>'
            f'<p>{_esc(s["paragraph_he"])}</p>'
            f'<p class="src">🔗 <a href="{_esc(s["source_url"])}" target="_blank" rel="noopener">{_esc(s["source_name"])}</a></p></article>'
        )
    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(BRAND_TITLE)} — {date_str}</title><style>{CSS}</style></head>
<body><div class="wrap">
<header><h1>🚴‍♂️ {_esc(BRAND_TITLE)}</h1><div class="date">{date_str}</div></header>
{_hero(image_url, image_credit)}
{''.join(blocks)}
<nav class="arch"><a href="index.html">הכתבה האחרונה</a> · <a href="archive.html">ארכיון</a></nav>
<footer>נוצר אוטומטית · הסיכומים בניסוח מקורי, קישור למקור בכל ידיעה</footer>
</div></body></html>"""


def _hero(image_url, credit):
    if not image_url:
        return ""
    return (
        f'<figure style="margin:16px 0 0"><img src="{_esc(image_url)}" alt="" '
        f'style="width:100%;border-radius:12px;display:block">'
        f'<figcaption style="color:#888;font-size:.8em;text-align:left;margin-top:4px">{_esc(credit)}</figcaption></figure>'
    )


def _rebuild_archive():
    files = sorted(
        f for f in os.listdir(DOCS_DIR)
        if f.endswith(".html") and f not in ("index.html", "archive.html")
    )
    links = "".join(
        f'<article><p class="src"><a href="{f}">📰 {f.replace(".html", "")}</a></p></article>'
        for f in reversed(files)
    )
    page = f"""<!DOCTYPE html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><title>ארכיון — {_esc(BRAND_TITLE)}</title>
<style>{CSS}</style></head><body><div class="wrap">
<header><h1>🚴‍♂️ ארכיון {_esc(BRAND_TITLE)}</h1></header>{links}
<nav class="arch"><a href="index.html">הכתבה האחרונה</a></nav></div></body></html>"""
    with open(os.path.join(DOCS_DIR, "archive.html"), "w", encoding="utf-8") as f:
        f.write(page)


def build_html(feature, stories, image_url=None, image_credit=""):
    il_now = datetime.now(timezone.utc) + timedelta(hours=3)  # שעון ישראל (קיץ)
    date_str = il_now.strftime("%d.%m.%Y")
    file_date = il_now.strftime("%Y-%m-%d")

    os.makedirs(DOCS_DIR, exist_ok=True)
    page = build_page(feature, stories, date_str, image_url, image_credit)

    daily_path = os.path.join(DOCS_DIR, f"{file_date}.html")
    for path in (daily_path, os.path.join(DOCS_DIR, "index.html")):
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
    _rebuild_archive()

    print(f"[html] נכתבו {daily_path} + index.html + archive.html")
    return daily_path, date_str
