# -*- coding: utf-8 -*-
"""הגדרות מרכזיות לסוכן חדשות האופניים."""

# 5 אתרי סיקור האופניים הגדולים בעולם (פידים אומתו)
SOURCES = [
    {"name": "Cyclingnews",       "feed": "https://www.cyclingnews.com/feeds.xml",   "site": "https://www.cyclingnews.com"},
    {"name": "Velo",              "feed": "https://www.velonews.com/feed/",          "site": "https://velo.outsideonline.com"},
    {"name": "Cycling Weekly",    "feed": "https://www.cyclingweekly.com/feeds.xml", "site": "https://www.cyclingweekly.com"},
    {"name": "Escape Collective", "feed": "https://escapecollective.com/rss",       "site": "https://escapecollective.com"},
    {"name": "road.cc",           "feed": "https://road.cc/feed",                    "site": "https://road.cc"},
]

# כמה שעות אחורה לאסוף ידיעות
HOURS_WINDOW = 30

# כמה ידיעות בכתבה היומית
NUM_STORIES = 5

# דגם Gemini (שכבה חינמית)
GEMINI_MODEL = "gemini-2.5-flash"

# כותרת המותג
BRAND_TITLE = "חדשות עולם האופניים"

# פוקוס עונתי: ידיעות טור דה פראנס מקבלות עדיפות עליונה (יולי)
TDF_FOCUS = True

# תקרת פריטים גולמיים שנשלחים ל-Gemini לדירוג
MAX_RAW_ITEMS = 40
