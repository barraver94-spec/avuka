# מניפסט שדות — טפסי כבאות אבוקה

מסמך זה מקשר בין שלושת הרכיבים: **כיול** (מיקומים, ב‑`calibrations/form{N}.json`) ←→ **נתונים** (base44) ←→ **גשר** (צומת "Build Render Payload" ב‑n8n).

כל שדה ברנדרר מזוהה לפי `id`, וזה גם **מפתח הנתון** שנשלף מ‑`data.common` (שדה בודד) או `data.rows` (שורת טבלה). כדי שטקסט יופיע — חייב להגיע ערך באותו מפתח מ‑n8n.

## מקרא סטטוס
- ✅ **זורם** — קיים ב‑base44 ונשלח כיום ע"י n8n.
- 🔑 **אי‑התאמת מפתח** — הערך זורם, אבל ה‑`id` בכיול שונה ממפתח n8n (צריך ליישר שם).
- 🔧 **מיפוי שגוי** — n8n שולף מהמקור הלא נכון (פרטי קשר נשלפים מ‑Customer במקום מ‑Contact).
- ⚠️ **קיים אך לא ממופה** — הנתון קיים ב‑base44, אבל n8n לא שולח אותו (צריך להוסיף לצומת Build Render Payload).
- ❌ **חסר** — אין שדה כזה ב‑base44 (צריך להוסיף שדה חדש).

---

## טופס 1 — גלגלונים וזרנוקים

### עמוד 1 — שדות בודדים (`common`)

| id בכיול | תווית | מפתח נתון | מקור ב‑base44 | סטטוס |
|---|---|---|---|---|
| date | תאריך | date | FireInspection.inspection_date | ✅ |
| business_name | שם העסק | business_name | FireInspection.customer_name / Customer.name | ✅ |
| business_type | מהות העסק | business_type | Customer.business_type | ✅ |
| vat | ח.פ/ע.מ/ת.ז | vat_number | Customer.vat_number | 🔑 |
| fire_file | מס׳ תיק כבאות | fire_file_number | FireInspection.fire_file_number / Site | 🔑 |
| city | יישוב | city | Site.city | ✅ |
| street | רחוב | street | Site.street | ✅ |
| house | מס׳ בית | house_number | Site.house_number | 🔑 |
| zip | מיקוד | zip | Site.zip | ✅ |
| po_box | ת״ד | — | — | ❌ (להוסיף Site.po_box) |
| contact_name | שם איש קשר | contact_name | Contact.full_name | 🔧 (n8n שולף מ‑Customer ריק) |
| contact_role | תפקיד | contact_role | Contact.role | 🔧 (n8n שולח ריק) |
| contact_phone | טלפון | contact_phone | Contact.phone | 🔧 (n8n שולף Customer.phone) |
| contact_email | דוא״ל | contact_email | Contact.email | 🔧 (n8n שולף Customer.email) |
| decl_name | הצהרה: שם מלא | decl_name | FireInspection.inspector_name | ⚠️ |
| decl_tz | הצהרה: ת.ז | decl_tz | FireInspection.inspector_id_number | ⚠️ |
| decl_date | הצהרה: תאריך | decl_date | FireInspection.inspection_date | ⚠️ |
| chk_zarnukim | ☑ זרנוקים | chk_zarnukim | — | ❌ (שדה boolean חדש) |
| chk_mitzmadim | ☑ מצמדים | chk_mitzmadim | — | ❌ |
| chk_maznakim | ☑ מזנקים | chk_maznakim | — | ❌ |
| chk_galgalon | ☑ גלגלון | chk_galgalon | — | ❌ |
| chk_acher | ☑ אחר | chk_acher | — | ❌ |
| acher_text | אחר (פירוט) | acher_text | — | ❌ |
| inspector_sig | חתימת הבודק | inspector_sig | FireInspection.inspector_name | ⚠️ |
| company_name | שם החברה | company_name | ברירת מחדל קבועה: "ר.אבוקה (1993) בע״מ" | ❌ (קבוע) |
| company_sig | חותמת חברה | — | תמונת חותמת | ❌ (מחוץ לטווח כרגע) |

### עמוד 2 — שדות בודדים
| id | תווית | מפתח | מקור | סטטוס |
|---|---|---|---|---|
| p2_fire_file | מס׳ תיק (עמ׳2) | fire_file_number | = fire_file | ⚠️ אותו ערך |
| p2_inspector_sig | חתימת הבודק (עמ׳2) | inspector_sig | FireInspection.inspector_name | ⚠️ |

### עמוד 2 — טבלה (`rows`, מ‑FireStation) — ✅ הכל זורם
num · location · hose · nozzle · cabinet · reel · notes
→ ממופים כיום ב‑n8n מ‑station_number/location/hose_2inch/nozzle_2inch/equipment_cabinet/hose_reel/notes.

---

## טופס 2 — מטפים מיטלטלים

עמוד 1 זהה לטופס 1 (אותם שדות `common`, אותם סטטוסים) — **ללא תיבות סימון** וללא acher.

### עמוד 2 — שדות כותרת/תחתית
| id | תווית | מפתח | מקור | סטטוס |
|---|---|---|---|---|
| p2_fire_file | מס׳ תיק (עמ׳2) | fire_file_number | = fire_file | ⚠️ |
| p2_customer_name | שם הלקוח (עמ׳2) | business_name | = business_name | ⚠️ |
| p2_page_num | דף מספר | page_num | חישוב (דף נוכחי) | ❌ (לוגיקת עמודים) |
| p2_page_total | מתוך (דפים) | page_total | חישוב (סה״כ דפים) | ❌ |
| p2_inspector_name | שם המבקר | inspector_sig | FireInspection.inspector_name | ⚠️ |
| p2_executor_sig | חתימת המבצע | inspector_sig | FireInspection.inspector_name | ⚠️ |
| p2_company_stamp | חותמת החברה | — | תמונת חותמת | ❌ |
| p2_date | תאריך (עמ׳2) | inspection_date | FireInspection.inspection_date | ⚠️ |

### עמוד 2 — טבלה (`rows`, מ‑FireExtinguisher)
| עמודה בכיול | מפתח n8n כיום | סטטוס |
|---|---|---|
| num, id, location, type, size_kg, manufacturer, next_major, next_pressure, insp_type | ✅ זורמים | ✅ |
| ok / not_ok (✓ תקין/פגום) | n8n שולח `status` (טקסט) במקום ok/not_ok | 🔧 לתקן: is_functional → ok='✓' או not_ok='✓' |
| notes | לא נשלח | ⚠️ להוסיף |

---

## תוכנית פעולה (3 שכבות)

**A. יישור מפתחות בכיול (קל, ללא שינוי n8n):** לשנות ב‑`form{N}.json` את ה‑id‑ים `vat→vat_number`, `house→house_number`, `fire_file→fire_file_number` (המיקומים לא משתנים). מסיר את כל ה‑🔑.

**B. base44 — שדות להוספה:**
- FireInspection: 5 שדות boolean לטופס 1 (`chk_zarnukim`, `chk_mitzmadim`, `chk_maznakim`, `chk_galgalon`, `chk_acher`) + `acher_text` (טקסט).
- Site: `po_box`.
- לוודא קישור Contact לכל FireInspection (לפרטי איש קשר).
- חותמת/לוגו חברה — להחליט אם תמונה או טקסט.

**C. n8n — להרחיב את "Build Render Payload":**
- להוסיף ל‑common: `decl_name`/`inspector_sig`/`p2_inspector_sig` ← inspector_name, `decl_tz` ← inspector_id_number, `decl_date`/`p2_date` ← inspection_date.
- לתקן פרטי קשר: לשלוף מ‑Contact (לחבר את צומת "Fetch Contact" שכרגע מנותק) במקום מ‑Customer.
- להוסיף את 6 שדות תיבות הסימון + acher_text מ‑FireInspection.
- טופס 2 טבלה: `is_functional` → `ok`/`not_ok` (✓) ולהוסיף `notes`.
- `company_name` ← קבוע "ר.אבוקה (1993) בע״מ".

> הערה: כל הקואורדינטות חיות ברנדרר (`calibrations/`), לא ב‑base44. base44 רק מחזיק נתונים; n8n ממפה אותם למפתחות שכאן.
