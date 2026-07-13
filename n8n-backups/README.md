# גיבויי n8n — לפני מחיקת החשבון

גיבוי של כל 11 הוורקפלואים מחשבון ה־n8n `avuka.app.n8n.cloud`, שיוצאו ב־13/07/2026 לקראת מחיקת החשבון. כל הוורקפלואים היו כבויים (unpublished) בעת הייצוא; הריצה האחרונה בחשבון הייתה ב־08/07/2026.

**אבטחה:** שני קבצים הכילו טוקנים מוטמעים בקוד הצמתים (Bearer של Base44 ומפתח anon של Supabase) — הם הוחלפו ב־`[REDACTED-...]`. שאר הוורקפלואים השתמשו ב־credentials של n8n (לפי הפניה בלבד), שאינם כלולים בייצוא ממילא.

## מיפוי: וורקפלואו → התחליף ב־Base44 (אפליקציית "אבוקה CRM")

| קובץ | וורקפלואו | תחליף |
|---|---|---|
| `NNVLdJ5y0JXZp9lR-whatsapp-ai-bot.json` | WhatsApp AI Bot — בוט שירות לקוחות בוואטסאפ (Twilio + Claude) | `base44/functions/whatsapp-bot` |
| `B9XKjpSy7MIaMZai-telegram-scheduler-bot.json` | לוז אבוקה — בוט טלגרם לעדכון לוז ב־Google Sheets | `base44/functions/telegram-scheduler-bot` (+ `telegram-webhook-admin`) |
| `gpKyvnY8cagWBdBf-daily-whatsapp-alerts.json` | התראה יומית בוואטסאפ על ביקורות ב־14 יום (08:00) | `base44/functions/daily-inspection-alerts` (תזמון: Base44 Automation) |
| `lgoI9CycD2suby6Y-notifications-dispatcher.json` | התראות קריאה חדשה (טלגרם + וואטסאפ למנהל) | `base44/functions/notify-new-call` |
| `KsyCVass1x41hgUX-pdf-renderer-pipeline-v2.json` | צינור הפקת PDF v2 — webhook → Renderer ב־Render.com → Supabase | `base44/functions/generateFormPdf` (קורא ישירות ל־Renderer) |
| `7LuL3yaOg6goT2vV-pdf-pipeline-v1.json` | צינור PDF v1 (HTML → Supabase) — הוחלף ע"י v2 | `generateFormPdf` / `generateMergedPdf` |
| `j6tehsj96cqIXzQF-pdf-import-fire-forms.json` | ייבוא PDF של טפסי אש — סיווג וחילוץ שדות עם Claude | `base44/functions/importFireFormPdf` + `extractFormPage` |
| `zMEb3Vy1CZu4EjS1-smart-request.json` | Smart Request — בקשה בשפה חופשית → FilledForms | `base44/functions/smart_certificate_engine` |
| `pivqBPFCggD9Tzm2-morning-schedule-draft-tasks.json` | לוז בוקר מ־Google Sheets → טיוטות ScheduledTask (07:30) | ללא תחליף ישיר (היה כבוי מ־28/06) |
| `tpZoUxro6mUPtCOw-cert-submission-email-secretary.json` | הגשת אישור → מייל למזכירה (ישן, ללא טריגר פעיל) | הוחלף ע"י זרימת ה־PDF החדשה |
| `EqhswSiMmJZ0Oiu5-temp-verify-certificates-table.json` | בדיקה זמנית של טבלת certificates | לא רלוונטי |

## שחזור

כל קובץ מכיל `nodes` + `connections` + `settings` וניתן לייבוא לכל מופע n8n (Import from File). לאחר ייבוא יש להגדיר מחדש credentials (Anthropic, Twilio, Telegram, Google Sheets OAuth, Supabase, Base44 token) ולהחליף את ה־`[REDACTED-...]` בערכים אמיתיים היכן שמופיע.
