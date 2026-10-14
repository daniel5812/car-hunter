# אימות car-hunter — 14.10.2026, Asia/Jerusalem

## מצב נוכחי — הסריקה מושבתת לבקשת המשתמש

ה־workflow הושבת ב־GitHub (disabled_manually). בזמן הכיבוי נמצאו אפס ריצות פעילות או ממתינות. תזמון כל שעתיים וטריגר push הוסרו, וה־job חסום גם בהפעלה ידנית. אין להפעיל מחדש לפני פתרון אמינות המקורות ואישור המשתמש. ההוכחות שלהלן הן היסטוריות ומוכיחות יכולת טכנית, לא אמינות של מקור המודעות.

## בדיקת שלושת המקורות בענן

[Source audit — הצלחה](https://github.com/daniel5812/car-hunter/actions/runs/38577469546)

Ubuntu של GitHub/Azure, ללא סשן מקומי או Secrets. נפתחו רשימה ושלוש מודעות
מכל אחד מ־ad, פוקוס ו־Zehcan ב־HTTP. לא נדרש Playwright.
דוח השדות, התאריכים, טלפונים ותנאי הגישה: [SOURCE_REPORT.md](SOURCE_REPORT.md).
פוקוס הוחרג מהמשך איסוף בשל איסור מפורש בתקנון שהוחזר בענן.
Zehcan נבחר למימוש; לא נמצא קישור לתנאים ו־robots מחזיר HTML,
ולכן לא נטען שקיים היתר מפורש.

## חיבור המסלול בפועל מתוך GitHub Actions

[הרצה מוצלחת ראשונה](https://github.com/daniel5812/car-hunter/actions/runs/38579111699)

```text
TELEGRAM zehcan/1651: ok message_id=4 demo=True
DATABASE zehcan rows=8
PIPELINE collected=8 inserted=8 updated=0 analyzed=8 cached=0 notified=1 failed=0
```

שמונה מודעות אמיתיות נשמרו ב־Neon עם psycopg, כל השמונה נותחו ב־DeepSeek
דרך ה־Secrets הקיימים ב־GitHub, והודעת הדגמה אחת הגיעה לטלגרם.
ההדגמה סומנה כבדיקת מסלול ללא התאמה מאושרת. בפורמט המחיר עם ₪ עדיין היה
חוסר בהרצה זו; הוא תוקן ונבדק בהרצות הבאות, בלי לשלוח הדגמה חוזרת.

[הרצה חוזרת — מחירים מלאים, מניעת כפילויות ומטמון](https://github.com/daniel5812/car-hunter/actions/runs/38579758050)

```text
COLLECT zehcan/1654: price=46000 year=2016 ... published=2026-10-11 ...
COLLECT zehcan/1651: price=89900 year=2023 ... published=2026-09-24 ...
DATABASE zehcan rows=8
PIPELINE collected=8 inserted=0 updated=8 analyzed=5 cached=3 notified=0 failed=0
```

אותן שמונה רשומות עודכנו; לא נוצרו כפילויות ולא נשלחה הודעה כפולה.

## הגרסה הסופית — עובדות מוכר מפורשות והסברי AI מוגבלים

[הרצה מוצלחת של הקוד הסופי](https://github.com/daniel5812/car-hunter/actions/runs/38581477446)

Commit קוד: 6ad75ea6e9e1a183c667c8f1fd5fb2892a21b0ea.
שינויים בתיעוד לאחר commit זה אינם משנים את הקוד שנבדק.

```text
Ran 21 tests in 0.085s
OK
COLLECT zehcan/1654: price=46000 year=2016 mileage=None location=None published=2026-10-11 updated=None seller=private phone=True
COLLECT zehcan/1652: price=8000 year=2012 mileage=145000 location=נאות מרדכי published=2026-10-01 updated=None seller=None phone=True
COLLECT zehcan/1651: price=89900 year=2023 mileage=95000 location=רמת גן published=2026-09-24 updated=None seller=None phone=True
COLLECT zehcan/1650: price=84900 year=2022 mileage=55000 location=רמת גן published=2026-09-24 updated=None seller=None phone=True
DATABASE zehcan rows=8
PIPELINE collected=8 inserted=0 updated=8 analyzed=8 cached=0 notified=0 failed=0
```

כל שמונה המודעות נאספו מחדש, והדירוגים חושבו מחדש בגלל שינוי גרסת prompt.
ב־1652 נשמר גיר ידני. בשבע האחרות הגיר חסר; אין מועמד עם אוטומט מפורש.
ב־1654 private הוא הצהרת "לא סוחר", לא אימות עצמאי.
מחיר 1652 בשדה סותר את התיאור, ויצרן 1651 סותר את שם הדגם; הסתירות נשמרו.

בדיקות אמת על HTML מהענן מכסות מחיר מלא מול תשלום חודשי, ₪, תאריכי מקור
מול כתבות מוטמעות ומועד איסוף, חסרים, קילומטראז׳ מול טווח חשמלי,
הצהרות מוכר, סתירות, pagination, ומניעת הסברי AI לא נתמכים.
בבדיקת תוכן דירוגים קודמים נמצאו הסקות שגויות של AI על מוכר פרטי,
גודל ו־2017 כתנאי סף. המימוש הסופי מאפשר בחירת הסברים רק מתוך רשימת
עובדות/חוסרים שנגזרה בקוד; מזהה הסבר שאינו ברשימה נדחה.
נבדקו גם הדירוגים שנשמרו בפועל לאחר שינוי זה.

## תזמון ומניעת חפיפות

בעבר workflow scan.yml הוגדר עם schedule כל שעתיים, בדקה 17 לפי UTC; התזמון הוסר לבקשת המשתמש.
הרצות GitHub מתוזמנות עלולות להתעכב; אין הבטחת שעת התחלה מדויקת.
concurrency group קבוע car-hunter-scan עם cancel-in-progress: false
מונע workflows חופפים. נעילת advisory של Postgres מגינה גם על שלב הכתיבה/דירוג.
הרצות האימות היו על push; התזמון אינו פעיל כעת.
התראות רגילות דורשות אוטומט מפורש ומעמד candidate, ולכן לא נשלחו המלצות
למודעות שבהן הגיר חסר או ידני. הדגמה חד־פעמית כבר הוכיחה את חיבור טלגרם.

## כשלים ומגבלות שנמצאו

- יד2: CAPTCHA; הומלס: 403/Cloudflare בבדיקה קודמת. אינם פעילים.
- פוקוס: נגיש טכנית, אבל תנאי איסוף אוטומטי מנעו בחירה בו; תאריכי מקור חסרים במדגם.
- ad: נגיש, אבל במדגם נמצאו מודעות מ־2025 וסתירות נתונים; לא נבחר כמקור ראשוני.
- [הרצת חיבור ראשונה שנכשלה](https://github.com/daniel5812/car-hunter/actions/runs/38578861845):
  בדיקת robots ציפתה לטקסט והמקור החזיר HTML עם 200. הטיפול תוקן, בלי להציג HTML כהיתר.
- פורמט מחיר עם ₪ זוהה בהרחבת האיסוף ותוקן; קישור pagination סונן.
- לא נקרא תאריך איסוף כתאריך פרסום, ולא הומצאו ק״מ/גיר/סוג מוכר.
- מודעות Zehcan מציגות תאריכי פרסום מספטמבר–אוקטובר 2026; דיוקם לא אומת מול המוכרים.
- אין עדיין מודעה שנאספה ועומדת באישור מפורש לדרישת האוטומט. יכולת האיסוף העצמאי
  והחיבור לכל השירותים הוכחה; איכות והתאמת המלאי הן מגבלה נפרדת.

## אבטחת קבצים ובדיקת מסד ראשונית

.env אינו tracked ומוחרג מ־Git. לא הודפסו סודות, ולא פורסם קובץ הסביבה.
צילומי אבחון מלאים נשמרים ב־artifacts המוחרגת; fixtures שנכנסו ל־Git מצונזרים.
ההרצה בענן משתמשת רק ב־GitHub Secrets ולא במחשב המקומי.

בבדיקה המקומית הראשונית SELECT 1 החזיר 1 דרך psycopg;
טבלת car_hunter_listings נוצרה. בדיקת insert/update/dedup בוטלה ב־rollback
והותירה אפס נתוני בדיקה. הודעת החיבור הראשונית "חיבור car-hunter תקין"
נשלחה פעם אחת, message_id=3. ממצאים אלו אינם מחליפים את הוכחת הענן לעיל.
