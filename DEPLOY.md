# Render.com Deployment Guide — Avuka PDF Renderer

## מה זה?
שרת Python/Flask שמקבל נתוני טופס, מציב אותם על רקעי הטפסים הרשמיים, ומחזיר PDF מקודד ב-base64.

---

## שלב 1 — צור GitHub repo

1. לך ל-https://github.com/new
2. שם: `avuka-renderer`
3. Private ✅
4. לחץ **Create repository**

## שלב 2 — העלה את הקבצים ל-GitHub

פתח Terminal בתיקייה הזו (`avuka-renderer`) והרץ:

```bash
git init
git add .
git commit -m "Initial avuka PDF renderer"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/avuka-renderer.git
git push -u origin main
```

> החלף `YOUR_USERNAME` בשם המשתמש שלך ב-GitHub.

---

## שלב 3 — Deploy ב-Render.com

1. לך ל-https://render.com → **New → Web Service**
2. חבר את ה-GitHub repo שיצרת
3. הגדרות:
   - **Name**: `avuka-pdf-renderer`
   - **Branch**: `main`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --timeout 120 --workers 2`
   - **Plan**: Free
4. לחץ **Create Web Service**

Render יעשה build אוטומטי. תוך ~3 דקות תקבל URL בפורמט:
```
https://avuka-pdf-renderer.onrender.com
```

---

## שלב 4 — עדכן את ה-URL בפונקציות Base44

> הערה היסטורית: בעבר הצינור עבר דרך n8n (workflow KsyCVass1x41hgUX). חשבון ה־n8n נמחק —
> גיבוי הוורקפלואים נמצא בתיקיית `n8n-backups/`. כיום Base44 קורא לרנדרר ישירות.

ברגע שיש לך את ה-URL מ-Render, עדכן את הקבוע `RENDERER_URL` בפונקציות
Base44 (אפליקציית "אבוקה CRM"):

- `base44/functions/generateFormPdf/entry.ts`
- `base44/functions/generateMergedPdf/entry.ts`
- `base44/functions/extractFormPage/entry.ts`

---

## שלב 5 — בדיקת Health

פתח בדפדפן:
```
https://avuka-pdf-renderer.onrender.com/health
```

אמור להחזיר:
```json
{"status": "ok", "forms": [1, 2, 3, 4, 5, 6, 7]}
```

---

## שלב 6 — בדיקה end-to-end

1. פתח את אפליקציית Base44 (אבוקה CRM)
2. בחר FilledForm קיים עם נתונים
3. לחץ **"הפק PDF"**
4. המתן ~10-30 שניות
5. כפתור **"הורד PDF"** אמור להופיע עם קישור לקובץ ב-Supabase

---

## פרטי הארכיטקטורה

```
Base44 [הפק PDF]
    ↓ base44.functions.invoke('generateFormPdf', { filled_form_id, form_num })
Base44 Function generateFormPdf
    ↓ Fetch FilledForm + Customer + Site
    ↓ Build payload { common, rows }
Render.com /render  ←── Flask + Pillow + PyMuPDF
    ↓ { pdf_base64, filename }
Supabase Edge Function upload-pdf
    ↓ Uploads to fire-forms bucket
    ↓ Returns public URL
generateFormPdf → עדכון FilledForm.generated_pdf = URL
Base44 → מציג כפתור הורדה
```

---

## שימו לב — Free Tier Render

ב-Free Plan, השרת "נרדם" אחרי 15 דקות ללא פעילות.
הבקשה הראשונה אחרי שינה לוקחת ~30 שניות (cold start).
לשימוש ייצורי — שדרג ל-Starter ($7/חודש) שתמיד פעיל.
