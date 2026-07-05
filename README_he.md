# סוכן "חדשות עולם האופניים" 🚴‍♂️

כתבה יומית בעברית (פוקוס טור דה פראנס) שרצה **בחינם בענן** — גם כשהמחשב כבוי.

## מה קורה כל בוקר (06:00 שעון ישראל בקיץ)
1. **איסוף** ידיעות מ-5 אתרי האופניים הגדולים בעולם (RSS, חלון 30 שעות): Cyclingnews, Velo, Cycling Weekly, Escape Collective, road.cc.
2. **Gemini 2.5 Flash** (שכבה חינמית) מדרג, מסכם ומתרגם לעברית 5 ידיעות — עדיפות עליונה לטור דה פראנס.
3. **כתבת HTML** (RTL) נשמרת ל-`docs/` ומתפרסמת ב-**GitHub Pages** — נפתחת בדפדפן מכל מכשיר, כולל ארכיון.
4. **טלגרם**: מקבץ הידיעות + קישור לכתבה + קובץ ה-HTML כמסמך.

## עלות: 0 ₪
GitHub Actions + GitHub Pages + Gemini free tier + Telegram Bot API — הכל חינם.

## Secrets (שלושה, תחת Settings → Secrets and variables → Actions)
| שם | ערך |
|----|-----|
| `GEMINI_API_KEY` | מפתח מ-aistudio.google.com |
| `TELEGRAM_BOT_TOKEN` | הבוט @shvoongtribot |
| `TELEGRAM_CHAT_ID` | `-1003843280663` |

## פריסה
1. repo **ציבורי** חדש (נדרש ל-Pages בחינם) → העלאת כל הקבצים.
2. הגדרת 3 ה-Secrets.
3. Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, תיקייה `/docs`.
4. Actions → daily-cycling-news → **Run workflow** לבדיקה.

## תזמון
Cron: `0 3 * * *` (UTC) = 06:00 בקיץ / 05:00 בחורף. GitHub לא מכיר שעון קיץ; לחורף אפשר לשנות ל-`0 4 * * *`. עיכובים של 5–15 דק' בעומס הם נורמליים.

## הערות
- כל שלב עטוף בטיפול שגיאות — פיד שנופל לא מפיל את הצינור.
- הסיכומים בניסוח מקורי + קישור למקור בכל ידיעה (זכויות יוצרים).
- הכתבות ב-Pages ציבוריות לכל מי שיש לו קישור.
- לערוץ טלגרם אחר: להחליף את `TELEGRAM_CHAT_ID`.
- בסוף הטור אפשר לכבות את הפוקוס: `TDF_FOCUS = False` ב-`config.py`.
