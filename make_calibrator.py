#!/usr/bin/env python3
"""
make_calibrator.py — Visual coordinate calibration for Avuka fire-form renderer.

Usage:  python3 make_calibrator.py
Output: calibrator.html  (open in Chrome)

Safety rules enforced:
  ✗  Does NOT write to app.py
  ✗  Does NOT deploy to Render
  ✗  Does NOT touch n8n workflows
  ✓  Only outputs calibrator.html and, when you press Export, downloads
     forms_config.calibrated.json to your Downloads folder.
"""
import os, base64, json, sys, webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_DIR   = os.path.join(BASE_DIR, 'backgrounds')
OUT_HTML = os.path.join(BASE_DIR, 'calibrator.html')
CFG_PATH = os.path.join(BASE_DIR, 'forms_config.json')

# ── Single source of truth ───────────────────────────────────────────────────
# All COORDINATES come from forms_config.json (the same file app.py loads).
# The literal dicts below that get overwritten from _BASE are kept ONLY as a
# structural reference; their numbers are ignored. UI labels/demos that the
# calibrator needs (and which the config does not carry, e.g. table columns)
# stay defined here and are merged onto the config positions at build time.
with open(CFG_PATH, encoding='utf-8') as _f:
    _BASE = json.load(_f)

# ── Page sizes (pt) ─────────────────────────────────────────────────────────
PORTRAIT  = [595.32, 841.92]
LANDSCAPE = [841.92, 595.32]

FORM_PAGES = {
    1: [PORTRAIT, LANDSCAPE],
    2: [PORTRAIT, LANDSCAPE],
    3: [PORTRAIT, PORTRAIT],
    4: [PORTRAIT, PORTRAIT, PORTRAIT, PORTRAIT],
    5: [PORTRAIT, PORTRAIT],
    6: [PORTRAIT, PORTRAIT],
    7: [PORTRAIT],
}

FORM_NAMES = {
    1: 'טופס 1 – עמדות כיבוי',
    2: 'טופס 2 – מטפים',
    3: 'טופס 3 – לוחות חשמל (גילוי)',
    4: 'טופס 4 – גילוי אש',
    5: 'טופס 5 – לוחות חשמל (כיבוי)',
    6: 'טופס 6 – כריזת חירום',
    7: 'טופס 7 – ספרינקלרים',
}

# ── Coordinates from forms_config.json (single source of truth) ──────────────
COLUMN_X = _BASE['COLUMN_X']
DATE_Y   = {int(k): v for k, v in _BASE['DATE_Y'].items()}
KLALI_Y  = {int(k): v for k, v in _BASE['KLALI_Y'].items()}

# Section-gim: form-specific page-1 fields
SECTION_GIM = {
    1: [
        {'id': 'inspector_name',   'label': 'שם בודק',       'x0': 373,   'y0': 697,   'x1': 477,   'y1': 708,   'demo': 'ישראל ישראלי'},
        {'id': 'business_name_sig','label': 'שם עסק חתימה',  'x0': 445,   'y0': 735,   'x1': 498,   'y1': 746,   'demo': 'מכולת כהן'},
    ],
    2: [
        {'id': 'inspector_name',   'label': 'שם בודק',        'x0': 346.9, 'y0': 409.3, 'x1': 431.9, 'y1': 422.3, 'demo': 'ישראל ישראלי'},
        {'id': 'inspector_id',     'label': 'ת.ז בודק',       'x0': 224.3, 'y0': 409.3, 'x1': 322.4, 'y1': 422.3, 'demo': '123456789'},
        {'id': 'date_decl',        'label': 'תאריך הצהרה',    'x0': 411.4, 'y0': 455.8, 'x1': 490.0, 'y1': 468.7, 'demo': '01/06/2025'},
        {'id': 'inspector_name_b', 'label': 'שם בודק (תחתון)','x0': 373,   'y0': 643,   'x1': 477,   'y1': 654,   'demo': 'ישראל ישראלי'},
        {'id': 'business_name_sig','label': 'שם עסק חתימה',   'x0': 386,   'y0': 681,   'x1': 497,   'y1': 692,   'demo': 'מכולת כהן'},
    ],
    3: [
        {'id': 'inspector_name',  'label': 'שם חשמלאי', 'x0': 358,   'y0': 383.4, 'x1': 443,   'y1': 396.4, 'demo': 'ישראל ישראלי'},
        {'id': 'inspector_id',    'label': 'ת.ז חשמלאי', 'x0': 245,   'y0': 383.4, 'x1': 330,   'y1': 396.4, 'demo': '123456789'},
        {'id': 'license_type',    'label': 'סוג רשיון',  'x0': 423,   'y0': 412.8, 'x1': 489,   'y1': 425.8, 'demo': 'ב'},
        {'id': 'license_number',  'label': 'מס רשיון',   'x0': 309,   'y0': 412.8, 'x1': 361,   'y1': 425.8, 'demo': 'A-1234'},
        {'id': 'date_decl',       'label': 'תאריך',      'x0': 420,   'y0': 444.9, 'x1': 486,   'y1': 457.8, 'demo': '01/06/2025'},
    ],
    4: [
        {'id': 'panel_type',           'label': 'סוג לוח',      'x0': 400, 'y0': 470.0, 'x1': 530, 'y1': 482.0, 'demo': 'אנלוגית'},
        {'id': 'panel_model',          'label': 'דגם',           'x0': 300, 'y0': 470.0, 'x1': 398, 'y1': 482.0, 'demo': 'DS7400'},
        {'id': 'panel_manufacturer',   'label': 'יצרן',          'x0': 150, 'y0': 470.0, 'x1': 298, 'y1': 482.0, 'demo': 'Bosch'},
        {'id': 'risk_level',           'label': 'רמת סיכון',     'x0': 440, 'y0': 493.0, 'x1': 520, 'y1': 505.0, 'demo': 'רמת סיכון I'},
        {'id': 'date',                 'label': 'תאריך',         'x0': 330, 'y0': 509.4, 'x1': 511, 'y1': 521.4, 'demo': '01/06/2025'},
        {'id': 'business_name',        'label': 'שם עסק',        'x0': 311, 'y0': 529.4, 'x1': 492, 'y1': 545.0, 'demo': 'מכולת כהן'},
        {'id': 'compliance_check_date','label': 'תאריך תקן',     'x0': 266, 'y0': 556.7, 'x1': 458, 'y1': 568.7, 'demo': '01/06/2025'},
    ],
    5: [
        {'id': 'property_holder_name', 'label': 'שם מחזיק',     'x0': 75,  'y0': 604, 'x1': 461, 'y1': 615, 'demo': 'יוסי לוי'},
        {'id': 'property_address',     'label': 'כתובת',         'x0': 73,  'y0': 630, 'x1': 485, 'y1': 641, 'demo': 'רוטשילד 10 ת"א'},
        {'id': 'maintenance_company',  'label': 'חברת תחזוקה',   'x0': 255, 'y0': 655, 'x1': 451, 'y1': 666, 'demo': 'ב.מ. בטיחות'},
        {'id': 'maintenance_phone',    'label': 'טלפון תחזוקה',  'x0': 71,  'y0': 655, 'x1': 254, 'y1': 666, 'demo': '03-1234567'},
        {'id': 'certification_number', 'label': 'מס תעודה',      'x0': 76,  'y0': 681, 'x1': 454, 'y1': 692, 'demo': 'T-123456'},
        {'id': 'technician_name',      'label': 'שם טכנאי',      'x0': 310, 'y0': 707, 'x1': 498, 'y1': 718, 'demo': 'מיכאל דוד'},
        {'id': 'technician_id',        'label': 'ת.ז טכנאי',     'x0': 82,  'y0': 707, 'x1': 263, 'y1': 718, 'demo': '123456789'},
    ],
    6: [
        {'id': 'route',          'label': 'מסלול',    'x0': 200, 'y0': 630, 'x1': 530, 'y1': 642, 'demo': 'ת"י 1220 חלק 3'},
        {'id': 'inspector_name', 'label': 'שם בודק',  'x0': 310, 'y0': 657, 'x1': 530, 'y1': 668, 'demo': 'ישראל ישראלי'},
        {'id': 'inspector_id',   'label': 'ת.ז בודק', 'x0': 100, 'y0': 657, 'x1': 295, 'y1': 668, 'demo': '123456789'},
    ],
    7: [
        {'id': 'property_holder_name', 'label': 'שם מחזיק',    'x0': 190, 'y0': 562, 'x1': 475, 'y1': 574, 'demo': 'יוסי לוי'},
        {'id': 'property_holder_id',   'label': 'ת.ז מחזיק',   'x0': 59,  'y0': 562, 'x1': 180, 'y1': 574, 'demo': '123456789'},
        {'id': 'property_address',     'label': 'כתובת',        'x0': 190, 'y0': 587, 'x1': 475, 'y1': 599, 'demo': 'רוטשילד 10 ת"א'},
        {'id': 'company_name',         'label': 'שם חברה',      'x0': 236, 'y0': 610, 'x1': 450, 'y1': 621, 'demo': 'ב.מ. בטיחות'},
        {'id': 'tav_teken_number',     'label': 'מס תו תקן',    'x0': 226, 'y0': 632, 'x1': 416, 'y1': 643, 'demo': 'TT-123'},
        {'id': 'water_source',         'label': 'מקור מים',     'x0': 62,  'y0': 632, 'x1': 180, 'y1': 643, 'demo': 'רשות המים'},
        {'id': 'technician_name',      'label': 'שם טכנאי',     'x0': 205, 'y0': 654, 'x1': 454, 'y1': 665, 'demo': 'מיכאל דוד'},
        {'id': 'pressure_low_psi',     'label': 'לחץ נמוך',     'x0': 300, 'y0': 676, 'x1': 400, 'y1': 687, 'demo': '50'},
        {'id': 'pressure_high_psi',    'label': 'לחץ גבוה',     'x0': 150, 'y0': 676, 'x1': 250, 'y1': 687, 'demo': '80'},
        {'id': 'is_functional',        'label': 'תקינות',       'x0': 200, 'y0': 700, 'x1': 450, 'y1': 712, 'demo': 'תקין'},
    ],
}

# Form 6 page 2: single-declaration fields
FORM6_P2 = [
    {'id': 'fire_file_header',    'label': 'מס תיק',            'x0': 459, 'y0': 100, 'x1': 574, 'y1': 113, 'demo': '12345'},
    {'id': 'inspector_name',      'label': 'שם בודק',           'x0': 190, 'y0': 163, 'x1': 435, 'y1': 175, 'demo': 'ישראל ישראלי'},
    {'id': 'license_number',      'label': 'מס רשיון',          'x0':  55, 'y0': 163, 'x1': 185, 'y1': 175, 'demo': 'A-1234'},
    {'id': 'license_expiry',      'label': 'תוקף רשיון',        'x0':  55, 'y0': 183, 'x1': 185, 'y1': 194, 'demo': '31/12/2025'},
    {'id': 'inspection_date',     'label': 'תאריך בדיקה',       'x0':  55, 'y0': 202, 'x1': 185, 'y1': 213, 'demo': '01/06/2025'},
    {'id': 'tav_teken_number',    'label': 'מס תו תקן',         'x0': 190, 'y0': 222, 'x1': 380, 'y1': 233, 'demo': 'TT-123'},
    {'id': 'tav_teken_expiry',    'label': 'תוקף תו תקן',       'x0':  55, 'y0': 222, 'x1': 185, 'y1': 233, 'demo': '31/12/2025'},
    {'id': 'conclusion_ok',       'label': 'תקינה ✓',           'x0': 200, 'y0': 238, 'x1': 340, 'y1': 250, 'demo': 'תקינה'},
    {'id': 'conclusion_not',      'label': 'לא תקינה (ריק כשתקין)', 'x0': 100, 'y0': 238, 'x1': 198, 'y1': 250, 'demo': ''},
    {'id': 'inspector_name_sig',  'label': 'שם בודק (חתימה)',   'x0': 310, 'y0': 488, 'x1': 530, 'y1': 500, 'demo': 'ישראל ישראלי'},
    {'id': 'inspector_id_sig',    'label': 'ת.ז (חתימה)',       'x0': 100, 'y0': 488, 'x1': 295, 'y1': 500, 'demo': '123456789'},
]

# ── Override coordinates from forms_config.json (single source of truth) ─────
# The SECTION_GIM / FORM6_P2 literals above are superseded by the config and
# are no longer used; the live values come from forms_config.json.
SECTION_GIM = {int(k): v for k, v in _BASE['SECTION_GIM'].items()}
FORM6_P2 = _BASE['FORM6_P2']

# UI_TABLES holds ONLY the column labels & demo strings for the calibrator UI.
# All table positions (left/width, max_rows, row_y, *_start_y, *_row_h, *_max)
# are taken from forms_config.json at build time and merged over these.
UI_TABLES = {
    1: {
        'fire_file_pos': {'left': 100, 'top': 90, 'width': 320, 'height': 13},
        'row_start_y': 174, 'row_height': 14, 'max_rows': 5,
        'columns': [
            {'key': 'num',      'label': 'מס',     'left': 784, 'width':  35, 'demo': '1'},
            {'key': 'location', 'label': 'מיקום',  'left': 580, 'width': 203, 'demo': 'כניסה ראשית'},
            {'key': 'hose',     'label': 'זרנוק',  'left': 518, 'width':  62, 'demo': 'V'},
            {'key': 'nozzle',   'label': 'מזנק',   'left': 454, 'width':  64, 'demo': 'V'},
            {'key': 'cabinet',  'label': 'ארון',   'left': 383, 'width':  71, 'demo': 'V'},
            {'key': 'reel',     'label': 'גלגלון', 'left': 312, 'width':  71, 'demo': 'V'},
            {'key': 'notes',    'label': 'הערות',  'left':  72, 'width': 241, 'demo': 'תקין'},
        ],
    },
    2: {
        'fire_file_pos': {'left': 429,   'top':  94.4, 'width': 124.4, 'height': 13},
        'biz_name_pos':  {'left': 496.3, 'top': 145.5, 'width': 183.1, 'height': 13},
        'row_y': [215.7, 230.6, 245.6, 260.4, 275.5, 290.5],
        'max_rows': 5,
        'columns': [
            {'key': 'num',          'label': 'מס',     'left': 782.3, 'width':  36.9, 'demo': '1'},
            {'key': 'id',           'label': 'מס סידורי','left': 726.6, 'width':  55.2, 'demo': 'P-001'},
            {'key': 'location',     'label': 'מיקום',  'left': 602.0, 'width': 124.1, 'demo': 'קומה 1'},
            {'key': 'type',         'label': 'סוג',    'left': 531.2, 'width':  70.3, 'demo': 'אבקה'},
            {'key': 'size_kg',      'label': 'משקל kg','left': 478.4, 'width':  52.3, 'demo': '6'},
            {'key': 'manufacturer', 'label': 'יצרן',   'left': 390.2, 'width':  87.7, 'demo': 'Safety'},
            {'key': 'next_major',   'label': 'בדיקה יסודית','left': 320.8, 'width':  68.9, 'demo': '06/2028'},
            {'key': 'next_pressure','label': 'בדיקת לחץ','left': 237.4, 'width':  83.4, 'demo': '06/2030'},
            {'key': 'ok',           'label': 'תקין ✓', 'left': 206.4, 'width':  30.5, 'demo': '✓'},
            {'key': 'not_ok',       'label': 'פגום ✓', 'left': 173.5, 'width':  32.4, 'demo': ''},
            {'key': 'insp_type',    'label': 'סוג בדיקה','left':  92.8, 'width':  80.3, 'demo': 'שוטפת'},
            {'key': 'notes',        'label': 'הערות',  'left':  25.0, 'width':  67.3, 'demo': ''},
        ],
    },
    3: {
        'fire_file_pos': {'left': 459, 'top': 100, 'width': 115, 'height': 13},
        'row_start_y': 212, 'row_height': 14, 'max_rows': 5,
        'columns': [
            {'key': 'num',        'label': 'מס',        'left': 461, 'width':  91, 'demo': '1'},
            {'key': 'location',   'label': 'מיקום',     'left': 369, 'width':  92, 'demo': 'מרתף'},
            {'key': 'amperage',   'label': 'אמפראז',    'left': 291, 'width':  78, 'demo': '200A'},
            {'key': 'disconnect', 'label': 'מנתק ✓',   'left': 173, 'width': 118, 'demo': '✓'},
            {'key': 'detection',  'label': 'גילוי ✓',  'left': 115, 'width':  58, 'demo': '✓'},
            {'key': 'suppress',   'label': 'כיבוי ✓',  'left':  57, 'width':  58, 'demo': ''},
        ],
    },
    4: {
        'fire_file_pos': {'left': 459, 'top': 100, 'width': 115, 'height': 13},
        'detector_start_y': 170, 'detector_row_h': 18, 'max_rows': 5,
        'detector_cols': [
            {'key': 'det_num',      'label': 'מס',        'left': 461, 'width':  60, 'demo': '1'},
            {'key': 'det_location', 'label': 'מיקום',     'left': 350, 'width': 110, 'demo': 'חדר שרתים'},
            {'key': 'det_type',     'label': 'סוג',       'left': 230, 'width': 119, 'demo': 'עשן'},
            {'key': 'det_zone',     'label': 'אזור',      'left': 140, 'width':  89, 'demo': '1'},
            {'key': 'det_status',   'label': 'תקינות',    'left':  30, 'width': 109, 'demo': 'תקין'},
        ],
        'phone_start_y': 160, 'phone_row_h': 18,
        'phone_cols': [
            {'key': 'ph_num',    'label': 'מס',    'left': 461, 'width':  60, 'demo': '1'},
            {'key': 'ph_number', 'label': 'מספר',  'left': 200, 'width': 260, 'demo': '02-1234567'},
            {'key': 'ph_note',   'label': 'הערה',  'left':  30, 'width': 169, 'demo': 'משטרה'},
        ],
        'defect_start_y': 160, 'defect_row_h': 18,
        'defect_cols': [
            {'key': 'def_num',  'label': 'מס',    'left': 461, 'width':  60, 'demo': '1'},
            {'key': 'def_desc', 'label': 'תיאור', 'left':  30, 'width': 430, 'demo': 'חיישן פגום בחדר 3'},
        ],
    },
    5: {
        'fire_file_pos': {'left': 459, 'top': 100, 'width': 115, 'height': 13},
        'row_start_y': 209, 'row_height': 22, 'max_rows': 5,
        'columns': [
            {'key': 'num',      'label': 'מס',       'left': 466, 'width':  86, 'demo': '1'},
            {'key': 'location', 'label': 'מיקום',    'left': 370, 'width':  96, 'demo': 'מרתף'},
            {'key': 'amperage', 'label': 'אמפראז',   'left': 307, 'width':  62, 'demo': '200A'},
            {'key': 'sup_type', 'label': 'סוג כיבוי','left': 266, 'width':  42, 'demo': 'גז'},
            {'key': 'weight',   'label': 'משקל g',   'left': 215, 'width':  51, 'demo': '5000'},
            {'key': 'status',   'label': 'תקינות',   'left':  95, 'width': 120, 'demo': 'תקין'},
        ],
    },
    6: {
        'fire_file_pos': {'left': 459, 'top': 100, 'width': 115, 'height': 13},
    },
    7: {},
}


def load_bg_b64(form_num, page_idx):
    path = os.path.join(BG_DIR, f'form{form_num}_page{page_idx + 1}.png')
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def build_js_config():
    """Build the full JS-embedded config dict."""
    # Backgrounds
    bgs = {}
    for fn, pages in FORM_PAGES.items():
        for pi in range(len(pages)):
            key = f'{fn}_{pi}'
            b64 = load_bg_b64(fn, pi)
            if b64:
                bgs[key] = b64
            else:
                print(f'  WARN: missing backgrounds/form{fn}_page{pi+1}.png')

    # Merge production table positions (from config) with UI labels/demos.
    full_tables = {str(k): v for k, v in _BASE['FORM_TABLES'].items()}
    merged_tables = json.loads(json.dumps(full_tables))  # deep copy (string keys)
    for fn, ui in UI_TABLES.items():
        bt = merged_tables.get(str(fn))
        if not bt:
            continue
        for colset in ('columns', 'detector_cols', 'phone_cols', 'defect_cols'):
            if colset in ui and colset in bt:
                ui_by_key = {c['key']: c for c in ui[colset]}
                for c in bt[colset]:
                    u = ui_by_key.get(c['key'])
                    if u:
                        if 'label' in u: c['label'] = u['label']
                        if 'demo'  in u: c['demo']  = u['demo']

    cfg = {
        'FORM_PAGES': {str(fn): [[w, h] for w, h in pages] for fn, pages in FORM_PAGES.items()},
        'FORM_NAMES': {str(k): v for k, v in FORM_NAMES.items()},
        # passthrough config keys so the exported JSON is a complete forms_config.json
        'page_sizes': _BASE['page_sizes'],
        'form_pages': _BASE['form_pages'],
        'COLUMN_X': COLUMN_X,
        'ID_BOXES_X': _BASE['ID_BOXES_X'],
        'FF_BOXES_X': _BASE['FF_BOXES_X'],
        'DATE_Y': {str(k): v for k, v in DATE_Y.items()},
        'KLALI_Y': {str(k): v for k, v in KLALI_Y.items()},
        'SECTION_GIM': {str(k): v for k, v in SECTION_GIM.items()},
        'FORM6_P2': FORM6_P2,
        'FORM_TABLES': {str(k): v for k, v in merged_tables.items()},
        'BACKGROUNDS': bgs,
    }
    return json.dumps(cfg, ensure_ascii=False, indent=2)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Avuka Form Calibrator</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
#toolbar { background: #16213e; padding: 8px 12px; display: flex; align-items: center; gap: 10px; flex-shrink: 0; border-bottom: 2px solid #0f3460; flex-wrap: wrap; }
#toolbar label { font-size: 12px; color: #aaa; }
#toolbar select, #toolbar input[type=range] { font-size: 12px; padding: 2px 4px; }
#toolbar button { font-size: 12px; padding: 4px 10px; border: none; border-radius: 4px; cursor: pointer; }
#btnExport { background: #e94560; color: #fff; font-weight: bold; }
#btnReset  { background: #444; color: #eee; }
.main { display: flex; flex: 1; overflow: hidden; }
#canvas-area { flex: 1; overflow: auto; background: #111; padding: 20px; position: relative; }
#page-wrap { position: relative; display: inline-block; transform-origin: top left; }
#page-bg { display: block; }
.field-box { position: absolute; border: 2px solid rgba(255,200,0,0.85); background: rgba(255,200,0,0.12);
             cursor: move; user-select: none; font-size: 9px; color: #fff;
             display: flex; align-items: center; justify-content: center; text-align: center; overflow: hidden;
             transition: border-color 0.1s; }
.field-box:hover { border-color: #fff; background: rgba(255,255,255,0.15); }
.field-box.selected { border: 2px solid #00e5ff; background: rgba(0,229,255,0.2); box-shadow: 0 0 6px #00e5ff; }
.field-box.common  { border-color: rgba(100,220,100,0.9); background: rgba(100,220,100,0.1); }
.field-box.common.selected { border-color: #00e5ff; background: rgba(0,229,255,0.2); }
.field-box .demo { font-size: 8px; color: #ffe; opacity: 0.8; pointer-events: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
.field-box .lbl { font-size: 7px; color: #aaf; opacity: 0.7; pointer-events: none; }
#sidebar { width: 260px; background: #16213e; border-right: 2px solid #0f3460; overflow-y: auto; padding: 10px; flex-shrink: 0; }
#sidebar h3 { font-size: 13px; color: #e94560; margin-bottom: 8px; }
#field-info { font-size: 11px; line-height: 1.6; }
#field-info .row { display: flex; justify-content: space-between; margin-bottom: 4px; }
#field-info input[type=number] { width: 70px; background: #0f3460; border: 1px solid #333; color: #fff; padding: 2px 4px; border-radius: 3px; font-size: 11px; }
#coord-display { font-family: monospace; font-size: 10px; color: #0f8; margin-top: 8px; padding: 6px; background: #0a0a1e; border-radius: 4px; line-height: 1.7; }
#hint { margin-top: 10px; font-size: 10px; color: #888; line-height: 1.5; }
#changes-count { font-size: 11px; color: #e94560; margin-top: 8px; }
.page-tabs { display: flex; gap: 4px; margin-top: 6px; }
.page-tab { padding: 4px 10px; border: 1px solid #333; border-radius: 4px; cursor: pointer; font-size: 11px; background: #222; color: #aaa; }
.page-tab.active { background: #0f3460; color: #fff; border-color: #0f8; }
</style>
</head>
<body>
<div id="toolbar">
  <label>טופס:</label>
  <select id="formSel"></select>
  <div class="page-tabs" id="pageTabs"></div>
  <label style="margin-right:10px">זום:</label>
  <input type="range" id="zoomSlider" min="30" max="150" value="75" style="width:100px">
  <span id="zoomLabel">75%</span>
  <button id="btnReset">Reset Changes</button>
  <button id="btnExport">⬇ Export JSON</button>
  <span id="changes-count"></span>
</div>
<div class="main">
  <div id="canvas-area">
    <div id="page-wrap">
      <img id="page-bg" src="" alt="background">
    </div>
  </div>
  <div id="sidebar">
    <h3>שדה נבחר</h3>
    <div id="field-info"><p style="color:#666">לחץ על שדה לבחירה</p></div>
    <div id="coord-display"></div>
    <div id="hint">
      <b>מקלדת:</b><br>
      ← → ↑ ↓ : הזזה 0.5pt<br>
      Shift+חץ : הזזה 5pt<br>
      Ctrl+← → : שינוי רוחב<br>
      Del / Backspace : ביטול בחירה
    </div>
  </div>
</div>
<script type="application/json" id="cfg-data">__CONFIG_JSON__</script>
<script>
const CFG = JSON.parse(document.getElementById('cfg-data').textContent);

// ── State ──────────────────────────────────────────────────────────────────
let currentForm = 1;
let currentPage = 0;
let zoom = 0.75;
let selectedId = null;
let isDragging = false;
let dragStart = { mx: 0, my: 0, ox0: 0, oy0: 0 };
const changes = {};   // key: fieldId → {x0,y0,x1,y1}
const fieldDefs = {}; // key: fieldId → field def object (mutable)

// ── Helpers ────────────────────────────────────────────────────────────────
const PT2PX = () => zoom * (96 / 72);

function getPageSize(fn, pi) {
  return CFG.FORM_PAGES[String(fn)][pi];
}

function fieldKey(id) { return `${currentForm}_${currentPage}_${id}`; }

function applyChange(id, coords) {
  changes[fieldKey(id)] = { ...coords, form: currentForm, page: currentPage, id };
  const def = fieldDefs[id];
  if (def) { def.x0 = coords.x0; def.y0 = coords.y0; def.x1 = coords.x1; def.y1 = coords.y1; }
  document.getElementById('changes-count').textContent =
    `${Object.keys(changes).length} שינוי/ים`;
}

// ── Build field definitions for current form/page ──────────────────────────
function buildFields(fn, pi) {
  const fields = [];
  const kly = CFG.KLALI_Y[String(fn)];
  const cx  = CFG.COLUMN_X;
  const dyArr = CFG.DATE_Y[String(fn)];

  if (pi === 0) {
    // Date
    if (dyArr) {
      fields.push({id:'date', label:'תאריך', x0:cx.DATE_X[0], y0:dyArr[0], x1:cx.DATE_X[1], y1:dyArr[1], demo:'01/06/2025', group:'common', varKey:'DATE_Y.'+fn});
    }
    if (kly) {
      const [by0,by1] = kly.biz;
      const [ay0,ay1] = kly.addr;
      const [cy0,cy1] = kly.cont;
      fields.push({id:'biz_ff', label:'מס תיק',    x0:cx.BIZ_FF[0],  y0:by0, x1:cx.BIZ_FF[1],  y1:by1, demo:'12345',        group:'common', varKey:'BIZ_FF+KLALI_Y.'+fn+'.biz'});
      fields.push({id:'biz_bn', label:'שם עסק',    x0:cx.BIZ_BN[0],  y0:by0, x1:cx.BIZ_BN[1],  y1:by1, demo:'מכולת כהן',    group:'common', varKey:'BIZ_BN+KLALI_Y.'+fn+'.biz'});
      fields.push({id:'biz_bt', label:'סוג עסק',   x0:cx.BIZ_BT[0],  y0:by0, x1:cx.BIZ_BT[1],  y1:by1, demo:'מסחרי',        group:'common', varKey:'BIZ_BT'});
      fields.push({id:'biz_id', label:'ח.פ/ע.מ',   x0:cx.BIZ_ID[0],  y0:by0, x1:cx.BIZ_ID[1],  y1:by1, demo:'514123456',    group:'common', varKey:'BIZ_ID'});
      fields.push({id:'addr_ci',label:'עיר',        x0:cx.ADDR_CI[0], y0:ay0, x1:cx.ADDR_CI[1], y1:ay1, demo:'תל אביב',      group:'common', varKey:'ADDR_CI'});
      fields.push({id:'addr_st',label:'רחוב',       x0:cx.ADDR_ST[0], y0:ay0, x1:cx.ADDR_ST[1], y1:ay1, demo:'רוטשילד',      group:'common', varKey:'ADDR_ST'});
      fields.push({id:'addr_hn',label:'מספר',       x0:cx.ADDR_HN[0], y0:ay0, x1:cx.ADDR_HN[1], y1:ay1, demo:'10',           group:'common', varKey:'ADDR_HN'});
      fields.push({id:'addr_zp',label:'מיקוד',      x0:cx.ADDR_ZP[0], y0:ay0, x1:cx.ADDR_ZP[1], y1:ay1, demo:'6688101',      group:'common', varKey:'ADDR_ZP'});
      fields.push({id:'cont_cn',label:'איש קשר',    x0:cx.CONT_CN[0], y0:cy0, x1:cx.CONT_CN[1], y1:cy1, demo:'יוסי כהן',    group:'common', varKey:'CONT_CN'});
      fields.push({id:'cont_cr',label:'תפקיד',      x0:cx.CONT_CR[0], y0:cy0, x1:cx.CONT_CR[1], y1:cy1, demo:'מנהל',        group:'common', varKey:'CONT_CR'});
      fields.push({id:'cont_cp',label:'טלפון',      x0:cx.CONT_CP[0], y0:cy0, x1:cx.CONT_CP[1], y1:cy1, demo:'052-1234567', group:'common', varKey:'CONT_CP'});
      fields.push({id:'cont_ce',label:'אימייל',     x0:cx.CONT_CE[0], y0:cy0, x1:cx.CONT_CE[1], y1:cy1, demo:'a@b.com',     group:'common', varKey:'CONT_CE'});
    }
    // Section gim
    const gim = CFG.SECTION_GIM[String(fn)] || [];
    for (const g of gim) {
      fields.push({...g, group:'gim', varKey:'SECTION_GIM.'+fn+'.'+g.id});
    }
  } else {
    // Table page
    const tc = CFG.FORM_TABLES[String(fn)] || {};
    if (tc.fire_file_pos) {
      const fp = tc.fire_file_pos;
      fields.push({id:'fire_file_header', label:'מס תיק', x0:fp.left, y0:fp.top, x1:fp.left+fp.width, y1:fp.top+fp.height, demo:'12345', group:'header', varKey:'FORM_TABLES.'+fn+'.fire_file_pos'});
    }
    if (fn===6 && pi===1) {
      for (const f of CFG.FORM6_P2) {
        fields.push({...f, group:'gim', varKey:'FORM6_P2.'+f.id});
      }
    } else if (fn===4) {
      if (pi===1) {
        // Detector columns
        const cols = tc.detector_cols || [];
        const sy = tc.detector_start_y || 170;
        const rh = tc.detector_row_h || 18;
        for (let row=0; row<3; row++) {
          for (const col of cols) {
            fields.push({id:`det_${col.key}_r${row}`, label:col.label+' '+(row+1),
              x0:col.left, y0:sy+row*rh, x1:col.left+col.width, y1:sy+row*rh+rh,
              demo:col.demo, group:'table', varKey:`FORM_TABLES.4.detector_cols.${col.key}`});
          }
        }
      } else if (pi===2) {
        const cols = tc.phone_cols || [];
        const sy = tc.phone_start_y || 160;
        const rh = tc.phone_row_h || 18;
        for (let row=0; row<3; row++) {
          for (const col of cols) {
            fields.push({id:`ph_${col.key}_r${row}`, label:col.label+' '+(row+1),
              x0:col.left, y0:sy+row*rh, x1:col.left+col.width, y1:sy+row*rh+rh,
              demo:col.demo, group:'table', varKey:`FORM_TABLES.4.phone_cols.${col.key}`});
          }
        }
      } else if (pi===3) {
        const cols = tc.defect_cols || [];
        const sy = tc.defect_start_y || 160;
        const rh = tc.defect_row_h || 18;
        for (let row=0; row<3; row++) {
          for (const col of cols) {
            fields.push({id:`def_${col.key}_r${row}`, label:col.label+' '+(row+1),
              x0:col.left, y0:sy+row*rh, x1:col.left+col.width, y1:sy+row*rh+rh,
              demo:col.demo, group:'table', varKey:`FORM_TABLES.4.defect_cols.${col.key}`});
          }
        }
      }
    } else {
      // Standard table (forms 1,2,3,5)
      const cols = tc.columns || [];
      const rowYArr = tc.row_y;
      const sy = tc.row_start_y || 200;
      const rh = tc.row_height || 14;
      const showRows = Math.min(tc.max_rows||5, 3);
      for (let row=0; row<showRows; row++) {
        let y0, y1;
        if (rowYArr) {
          y0 = rowYArr[row]; y1 = rowYArr[row+1] || y0+14;
        } else {
          y0 = sy + row*rh; y1 = y0 + rh;
        }
        for (const col of cols) {
          fields.push({id:`col_${col.key}_r${row}`, label:col.label+' '+(row+1),
            x0:col.left, y0, x1:col.left+col.width, y1,
            demo:col.demo, group:'table', varKey:`FORM_TABLES.${fn}.columns.${col.key}`});
        }
      }
      // Also show biz_name_pos for form2
      if (fn===2 && tc.biz_name_pos) {
        const bp = tc.biz_name_pos;
        fields.push({id:'biz_name_header', label:'שם עסק (כותרת)', x0:bp.left, y0:bp.top, x1:bp.left+bp.width, y1:bp.top+bp.height, demo:'מכולת כהן', group:'header', varKey:'FORM_TABLES.2.biz_name_pos'});
      }
    }
  }
  return fields;
}

// ── Render page ────────────────────────────────────────────────────────────
function renderPage() {
  const wrap = document.getElementById('page-wrap');
  const bgImg = document.getElementById('page-bg');
  const [pw, ph] = getPageSize(currentForm, currentPage);
  const scale = PT2PX();

  const bgKey = `${currentForm}_${currentPage}`;
  const b64 = CFG.BACKGROUNDS[bgKey];
  if (b64) {
    bgImg.src = `data:image/png;base64,${b64}`;
  } else {
    bgImg.src = '';
    bgImg.style.background = '#fff';
  }
  bgImg.style.width  = (pw * scale) + 'px';
  bgImg.style.height = (ph * scale) + 'px';
  wrap.style.width  = (pw * scale) + 'px';
  wrap.style.height = (ph * scale) + 'px';

  // Remove old field boxes
  wrap.querySelectorAll('.field-box').forEach(el => el.remove());

  // Build fresh field defs
  Object.keys(fieldDefs).forEach(k => delete fieldDefs[k]);
  const fields = buildFields(currentForm, currentPage);

  // Apply any saved changes
  for (const f of fields) {
    const ck = `${currentForm}_${currentPage}_${f.id}`;
    if (changes[ck]) { f.x0=changes[ck].x0; f.y0=changes[ck].y0; f.x1=changes[ck].x1; f.y1=changes[ck].y1; }
    fieldDefs[f.id] = { ...f };
  }

  // Render boxes
  for (const f of fields) {
    const el = document.createElement('div');
    el.className = 'field-box' + (f.group === 'common' || f.group === 'header' ? ' common' : '');
    el.id = 'fb_' + f.id;
    el.dataset.fid = f.id;
    el.style.left   = (f.x0 * scale) + 'px';
    el.style.top    = (f.y0 * scale) + 'px';
    el.style.width  = ((f.x1 - f.x0) * scale) + 'px';
    el.style.height = ((f.y1 - f.y0) * scale) + 'px';
    el.innerHTML = `<span class="lbl">${f.label}</span>`;
    if (f.demo) el.innerHTML += `<br><span class="demo">${f.demo}</span>`;
    el.addEventListener('mousedown', onBoxMouseDown);
    wrap.appendChild(el);
  }

  if (selectedId) selectField(selectedId);
}

function selectField(id) {
  document.querySelectorAll('.field-box').forEach(el => el.classList.remove('selected'));
  selectedId = id;
  const el = document.getElementById('fb_' + id);
  if (el) el.classList.add('selected');
  updateSidebar();
}

function updateSidebar() {
  const info = document.getElementById('field-info');
  const coord = document.getElementById('coord-display');
  if (!selectedId || !fieldDefs[selectedId]) {
    info.innerHTML = '<p style="color:#666">לחץ על שדה לבחירה</p>';
    coord.textContent = '';
    return;
  }
  const f = fieldDefs[selectedId];
  info.innerHTML = `
    <b>${f.label}</b><br>
    <span style="color:#888;font-size:10px">var: ${f.varKey||f.id}</span><br><br>
    <div class="row"><label>x0</label><input type="number" id="i_x0" step="0.1" value="${f.x0.toFixed(1)}"></div>
    <div class="row"><label>y0</label><input type="number" id="i_y0" step="0.1" value="${f.y0.toFixed(1)}"></div>
    <div class="row"><label>x1</label><input type="number" id="i_x1" step="0.1" value="${f.x1.toFixed(1)}"></div>
    <div class="row"><label>y1</label><input type="number" id="i_y1" step="0.1" value="${f.y1.toFixed(1)}"></div>
  `;
  ['x0','y0','x1','y1'].forEach(k => {
    document.getElementById('i_'+k).addEventListener('change', () => {
      const fd = fieldDefs[selectedId];
      fd[k] = parseFloat(document.getElementById('i_'+k).value);
      applyChange(selectedId, {x0:fd.x0,y0:fd.y0,x1:fd.x1,y1:fd.y1});
      refreshBoxPos(selectedId);
      showCoord(fd);
    });
  });
  showCoord(f);
}

function showCoord(f) {
  document.getElementById('coord-display').textContent =
    `x0=${f.x0.toFixed(1)}  y0=${f.y0.toFixed(1)}\nx1=${f.x1.toFixed(1)}  y1=${f.y1.toFixed(1)}\nw=${(f.x1-f.x0).toFixed(1)}  h=${(f.y1-f.y0).toFixed(1)} pt`;
}

function refreshBoxPos(id) {
  const f = fieldDefs[id];
  if (!f) return;
  const el = document.getElementById('fb_' + id);
  if (!el) return;
  const scale = PT2PX();
  el.style.left   = (f.x0 * scale) + 'px';
  el.style.top    = (f.y0 * scale) + 'px';
  el.style.width  = ((f.x1 - f.x0) * scale) + 'px';
  el.style.height = ((f.y1 - f.y0) * scale) + 'px';
}

// ── Drag ──────────────────────────────────────────────────────────────────
function onBoxMouseDown(e) {
  e.stopPropagation();
  const id = e.currentTarget.dataset.fid;
  selectField(id);
  isDragging = true;
  const f = fieldDefs[id];
  dragStart = { mx: e.clientX, my: e.clientY, ox0: f.x0, oy0: f.y0, ox1: f.x1, oy1: f.y1 };
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup',   onMouseUp);
}

function onMouseMove(e) {
  if (!isDragging || !selectedId) return;
  const scale = PT2PX();
  const dx = (e.clientX - dragStart.mx) / scale;
  const dy = (e.clientY - dragStart.my) / scale;
  const f = fieldDefs[selectedId];
  const w = dragStart.ox1 - dragStart.ox0;
  const h = dragStart.oy1 - dragStart.oy0;
  f.x0 = Math.round((dragStart.ox0 + dx) * 10) / 10;
  f.y0 = Math.round((dragStart.oy0 + dy) * 10) / 10;
  f.x1 = f.x0 + w;
  f.y1 = f.y0 + h;
  refreshBoxPos(selectedId);
  showCoord(f);
}

function onMouseUp() {
  if (isDragging && selectedId) {
    const f = fieldDefs[selectedId];
    applyChange(selectedId, {x0:f.x0, y0:f.y0, x1:f.x1, y1:f.y1});
    updateSidebar();
  }
  isDragging = false;
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mouseup',   onMouseUp);
}

// ── Keyboard ──────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (!selectedId || !fieldDefs[selectedId]) return;
  if (['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)) return;
  const f = fieldDefs[selectedId];
  const step = e.shiftKey ? 5 : 0.5;
  let handled = true;
  if (e.key === 'ArrowLeft'  && !e.ctrlKey) { f.x0 -= step; f.x1 -= step; }
  else if (e.key === 'ArrowRight' && !e.ctrlKey) { f.x0 += step; f.x1 += step; }
  else if (e.key === 'ArrowUp')    { f.y0 -= step; f.y1 -= step; }
  else if (e.key === 'ArrowDown')  { f.y0 += step; f.y1 += step; }
  else if (e.key === 'ArrowLeft'  && e.ctrlKey)  { f.x1 -= step; }
  else if (e.key === 'ArrowRight' && e.ctrlKey)  { f.x1 += step; }
  else if (e.key === 'Delete' || e.key === 'Backspace') { selectedId = null; document.querySelectorAll('.field-box').forEach(el=>el.classList.remove('selected')); updateSidebar(); }
  else handled = false;
  if (handled) {
    e.preventDefault();
    f.x0 = Math.round(f.x0*10)/10; f.y0 = Math.round(f.y0*10)/10;
    f.x1 = Math.round(f.x1*10)/10; f.y1 = Math.round(f.y1*10)/10;
    refreshBoxPos(selectedId);
    applyChange(selectedId, {x0:f.x0,y0:f.y0,x1:f.x1,y1:f.y1});
    updateSidebar();
  }
});

// ── Export ────────────────────────────────────────────────────────────────
function buildExport() {
  // Start from original values and apply changes
  const out = {
    _version: '2.0',
    _generated: new Date().toISOString().slice(0,10),
    _note: 'Drop-in replacement for forms_config.json — save as forms_config.json next to app.py.',
    page_sizes: JSON.parse(JSON.stringify(CFG.page_sizes)),
    form_pages: JSON.parse(JSON.stringify(CFG.form_pages)),
    COLUMN_X: JSON.parse(JSON.stringify(CFG.COLUMN_X)),
    ID_BOXES_X: JSON.parse(JSON.stringify(CFG.ID_BOXES_X)),
    FF_BOXES_X: JSON.parse(JSON.stringify(CFG.FF_BOXES_X)),
    DATE_Y: JSON.parse(JSON.stringify(CFG.DATE_Y)),
    KLALI_Y: JSON.parse(JSON.stringify(CFG.KLALI_Y)),
    SECTION_GIM: JSON.parse(JSON.stringify(CFG.SECTION_GIM)),
    FORM6_P2: JSON.parse(JSON.stringify(CFG.FORM6_P2)),
    FORM_TABLES: JSON.parse(JSON.stringify(CFG.FORM_TABLES)),
  };

  // Apply changes back to export
  for (const [ck, change] of Object.entries(changes)) {
    const {form, page, id} = change;
    const fn = String(form);
    const coords = {x0:change.x0, y0:change.y0, x1:change.x1, y1:change.y1};

    if (page === 0) {
      // Map known IDs to their export paths
      const kly = out.KLALI_Y[fn];
      const cx  = out.COLUMN_X;
      const dateY = out.DATE_Y[fn];

      if (id === 'date' && dateY)                  { out.DATE_Y[fn] = [coords.y0, coords.y1]; cx.DATE_X = [coords.x0, coords.x1]; }
      else if (id === 'biz_ff' && kly)             { cx.BIZ_FF = [coords.x0, coords.x1]; kly.biz = [coords.y0, coords.y1]; }
      else if (id === 'biz_bn')                    { cx.BIZ_BN = [coords.x0, coords.x1]; }
      else if (id === 'biz_bt')                    { cx.BIZ_BT = [coords.x0, coords.x1]; }
      else if (id === 'biz_id')                    { cx.BIZ_ID = [coords.x0, coords.x1]; if(kly) kly.biz = [coords.y0, coords.y1]; }
      else if (id === 'addr_ci')                   { cx.ADDR_CI = [coords.x0, coords.x1]; if(kly) kly.addr = [coords.y0, coords.y1]; }
      else if (id === 'addr_st')                   { cx.ADDR_ST = [coords.x0, coords.x1]; }
      else if (id === 'addr_hn')                   { cx.ADDR_HN = [coords.x0, coords.x1]; }
      else if (id === 'addr_zp')                   { cx.ADDR_ZP = [coords.x0, coords.x1]; }
      else if (id === 'cont_cn')                   { cx.CONT_CN = [coords.x0, coords.x1]; if(kly) kly.cont = [coords.y0, coords.y1]; }
      else if (id === 'cont_cr')                   { cx.CONT_CR = [coords.x0, coords.x1]; }
      else if (id === 'cont_cp')                   { cx.CONT_CP = [coords.x0, coords.x1]; }
      else if (id === 'cont_ce')                   { cx.CONT_CE = [coords.x0, coords.x1]; }
      else {
        // Section gim
        const gim = out.SECTION_GIM[fn];
        if (gim) {
          const entry = gim.find(g => g.id === id);
          if (entry) { entry.x0=coords.x0; entry.y0=coords.y0; entry.x1=coords.x1; entry.y1=coords.y1; }
        }
      }
    } else {
      // Page 2+ → update FORM_TABLES or FORM6_P2
      const tc = out.FORM_TABLES[fn];
      if (fn === '6' && page === 1) {
        const entry = out.FORM6_P2.find(f => f.id === id);
        if (entry) { entry.x0=coords.x0; entry.y0=coords.y0; entry.x1=coords.x1; entry.y1=coords.y1; }
      } else if (tc) {
        // fire_file_header
        if (id === 'fire_file_header' && tc.fire_file_pos) {
          tc.fire_file_pos = {left:coords.x0, top:coords.y0, width:coords.x1-coords.x0, height:coords.y1-coords.y0};
        } else if (id === 'biz_name_header' && tc.biz_name_pos) {
          tc.biz_name_pos = {left:coords.x0, top:coords.y0, width:coords.x1-coords.x0, height:coords.y1-coords.y0};
        } else {
          // Column update: id like col_{key}_r0 → just update left/width for key
          const colMatch = id.match(/^col_(.+?)_r(\d+)$/);
          if (colMatch && page > 0) {
            const key = colMatch[1];
            const cols = tc.columns || tc.detector_cols || tc.phone_cols || tc.defect_cols;
            if (cols) {
              const col = cols.find(c => c.key === key);
              if (col) { col.left = coords.x0; col.width = coords.x1 - coords.x0; }
            }
          }
          // Detector / phone / defect columns
          const detMatch = id.match(/^det_(.+?)_r\d+$/);
          if (detMatch && tc.detector_cols) {
            const key = detMatch[1].replace('det_','');
            const col = tc.detector_cols.find(c=>c.key==='det_'+key);
            if (col) { col.left=coords.x0; col.width=coords.x1-coords.x0; }
          }
          const phMatch = id.match(/^ph_(.+?)_r\d+$/);
          if (phMatch && tc.phone_cols) {
            const key = phMatch[1].replace('ph_','');
            const col = tc.phone_cols.find(c=>c.key==='ph_'+key);
            if (col) { col.left=coords.x0; col.width=coords.x1-coords.x0; }
          }
          const defMatch = id.match(/^def_(.+?)_r\d+$/);
          if (defMatch && tc.defect_cols) {
            const key = defMatch[1].replace('def_','');
            const col = tc.defect_cols.find(c=>c.key==='def_'+key);
            if (col) { col.left=coords.x0; col.width=coords.x1-coords.x0; }
          }
          // Row position updates: update row_start_y / row_height from row 0
          // (simplification: changes to row 0 y set the start_y)
          const r0Match = id.match(/^col_.+_r0$/);
          if (r0Match && tc) {
            tc.row_start_y = coords.y0;
            if (tc.row_height) tc.row_height = coords.y1 - coords.y0;
          }
        }
      }
    }
  }
  return out;
}

document.getElementById('btnExport').addEventListener('click', () => {
  const out = buildExport();
  const json = JSON.stringify(out, null, 2);
  const blob = new Blob([json], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'forms_config.calibrated.json';
  a.click();
  alert('✓ יוצא: forms_config.calibrated.json\n\nזהו קובץ forms_config.json מלא ומעודכן.\nלהחלה: בדוק אותו, ואז שמור אותו בשם forms_config.json ליד app.py (החלף את הקיים).');
});

document.getElementById('btnReset').addEventListener('click', () => {
  if (!confirm('לאפס את כל השינויים?')) return;
  Object.keys(changes).forEach(k => delete changes[k]);
  document.getElementById('changes-count').textContent = '';
  selectedId = null;
  renderPage();
});

// ── Controls ──────────────────────────────────────────────────────────────
function populateFormSel() {
  const sel = document.getElementById('formSel');
  sel.innerHTML = '';
  for (let fn=1; fn<=7; fn++) {
    const opt = document.createElement('option');
    opt.value = fn;
    opt.textContent = CFG.FORM_NAMES[String(fn)] || 'טופס '+fn;
    sel.appendChild(opt);
  }
  sel.addEventListener('change', () => {
    currentForm = parseInt(sel.value);
    currentPage = 0;
    selectedId = null;
    buildPageTabs();
    renderPage();
  });
}

function buildPageTabs() {
  const tabs = document.getElementById('pageTabs');
  tabs.innerHTML = '';
  const pages = CFG.FORM_PAGES[String(currentForm)] || [];
  const labels = ['עמוד 1', 'עמוד 2', 'עמוד 3', 'עמוד 4'];
  pages.forEach((_, pi) => {
    const btn = document.createElement('div');
    btn.className = 'page-tab' + (pi===currentPage ? ' active' : '');
    btn.textContent = labels[pi] || `עמוד ${pi+1}`;
    btn.addEventListener('click', () => {
      currentPage = pi;
      selectedId = null;
      document.querySelectorAll('.page-tab').forEach(t=>t.classList.remove('active'));
      btn.classList.add('active');
      renderPage();
    });
    tabs.appendChild(btn);
  });
}

document.getElementById('zoomSlider').addEventListener('input', e => {
  zoom = parseInt(e.target.value) / 100;
  document.getElementById('zoomLabel').textContent = e.target.value + '%';
  renderPage();
});

// ── Init ──────────────────────────────────────────────────────────────────
populateFormSel();
buildPageTabs();
renderPage();
</script>
</body>
</html>"""


def main():
    print('Building calibrator…')
    js_cfg = build_js_config()
    # Embed JSON inside a <script type="application/json"> block (parsed via
    # textContent). This is immune to template-literal escaping issues with
    # backslashes / quotes in the data. Only guard against an accidental
    # </script> sequence (none in this data, but be safe).
    html = HTML_TEMPLATE.replace('__CONFIG_JSON__', js_cfg.replace('</', '<\\/'))
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓  Written: {OUT_HTML}')
    print('Opening in browser…')
    webbrowser.open('file:///' + OUT_HTML.replace('\\', '/'))


if __name__ == '__main__':
    main()
