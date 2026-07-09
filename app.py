"""
Avuka Fire Forms — PDF Renderer v4
Approach: fitz (PyMuPDF) + insert_htmlbox for accurate Hebrew RTL text.
Background PNGs from backgrounds/ are embedded as PDF page backgrounds.

POST /render  →  { form_num, data: {common, rows} }  →  { pdf_base64, filename }
GET  /health  →  { status: "ok" }

Field-name contract (matches Base44 schema exactly):
  Form 1  → FireStation rows
  Form 2  → FireExtinguisher rows
  Form 3  → ElectricalPanel rows (form_type="3")
  Form 4  → FireDetectionData rows[0]  (single record, JSON sub-fields parsed here)
  Form 5  → ElectricalPanel rows (form_type="5")
  Form 6  → EmergencyAnnouncementData rows[0]  (single record)
  Form 7  → SprinklerData rows[0]  (single record)

──────────────────────────────────────────────────────────────────────────────
SINGLE SOURCE OF TRUTH:
  All field COORDINATES are loaded from forms_config.json (next to this file).
  The visual calibrator (make_calibrator.py → calibrator.html) reads and writes
  that same file, so calibration changes flow here automatically — no manual
  porting. The logic (which data value goes to which field, value formatting)
  stays in this file; only the numbers live in the config.
──────────────────────────────────────────────────────────────────────────────
"""
import os, io, base64, traceback, re, json
import fitz
from flask import Flask, request, jsonify

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_DIR   = os.path.join(BASE_DIR, 'backgrounds')
CFG_PATH = os.path.join(BASE_DIR, 'forms_config.json')

# ── Load coordinate config (single source of truth) ──────────────────────────
with open(CFG_PATH, encoding='utf-8') as _f:
    CFG = json.load(_f)

# ── Page sizes ───────────────────────────────────────────────────────────────
PORTRAIT  = tuple(CFG['page_sizes']['portrait'])    # (595.32, 841.92)
LANDSCAPE = tuple(CFG['page_sizes']['landscape'])   # (841.92, 595.32)
_PAGE_KIND = {'portrait': PORTRAIT, 'landscape': LANDSCAPE}
FORM_PAGES = {int(k): [_PAGE_KIND[p] for p in v] for k, v in CFG['form_pages'].items()}

# ── Core insert helper ───────────────────────────────────────────────────────
def ic(page, x0, y0, x1, y1, text, fs=9, align="center"):
    """Insert Hebrew RTL text into rect (x0,y0,x1,y1) in pt."""
    if not text:
        return
    text = str(text)
    h = max(y1 - y0, 6)
    html = (
        f'<p dir="rtl" style="font-family: Arial, sans-serif; '
        f'font-size: {fs}px; font-weight: normal; '
        f'text-align: {align}; margin: 0; padding: 0; '
        f'line-height: {h}px;">{text}</p>'
    )
    page.insert_htmlbox(fitz.Rect(x0, y0, x1, y1), html)


# ── Digit-box helpers ────────────────────────────────────────────────────────
# BIZ_ID (ח.פ.) — 11 individual boxes extracted from form background PNG
ID_BOXES_X  = CFG['ID_BOXES_X']
# BIZ_FF (מס' תיק) — 10 individual boxes
FF_BOXES_X  = CFG['FF_BOXES_X']

def ic_digits(page, boxes_x, y0, y1, value, fs=8):
    """Place each character of value into its own cell (left-to-right)."""
    s = str(value).strip() if value else ''
    n = len(boxes_x) - 1
    for i, ch in enumerate(s[:n]):
        ic(page, boxes_x[i] + 0.5, y0, boxes_x[i+1] - 0.5, y1, ch, fs=fs, align='center')


# ── Klali table column X boundaries ─────────────────────────────────────────
_CX = CFG['COLUMN_X']
# Biz row (RTL: fire_file | business_name | business_type | customer_id)
BIZ_FF = tuple(_CX['BIZ_FF'])   # fire_file_number
BIZ_BN = tuple(_CX['BIZ_BN'])   # business_name
BIZ_BT = tuple(_CX['BIZ_BT'])   # business_type
BIZ_ID = tuple(_CX['BIZ_ID'])   # customer_id / ח.פ. / ע.מ.

# Address row (RTL: city | street | house_number | zip | po_box)
ADDR_CI = tuple(_CX['ADDR_CI'])  # city
ADDR_ST = tuple(_CX['ADDR_ST'])  # street
ADDR_HN = tuple(_CX['ADDR_HN'])  # house_number
ADDR_ZP = tuple(_CX['ADDR_ZP'])  # zip
ADDR_PB = tuple(_CX['ADDR_PB'])  # po_box

# Contact row (RTL: contact_name | contact_role | contact_phone | contact_email)
CONT_CN = tuple(_CX['CONT_CN'])  # contact_name
CONT_CR = tuple(_CX['CONT_CR'])  # contact_role
CONT_CP = tuple(_CX['CONT_CP'])  # contact_phone
CONT_CE = tuple(_CX['CONT_CE'])  # contact_email

# ── Per-form Y ranges for klali rows ─────────────────────────────────────────
KLALI_Y = {int(k): {kk: tuple(vv) for kk, vv in v.items()} for k, v in CFG['KLALI_Y'].items()}

# ── Per-form Y range for date field ──────────────────────────────────────────
DATE_Y = {int(k): tuple(v) for k, v in CFG['DATE_Y'].items()}
DATE_X = tuple(_CX['DATE_X'])

# ── Section-gim (page-1 form-specific fields) & Form-6 page-2 positions ───────
# Indexed by field id → (x0, y0, x1, y1). Coordinates only; value logic in code.
SECTION_GIM = {
    int(k): {f['id']: (f['x0'], f['y0'], f['x1'], f['y1']) for f in v}
    for k, v in CFG['SECTION_GIM'].items()
}
FORM6_P2 = {f['id']: (f['x0'], f['y0'], f['x1'], f['y1']) for f in CFG['FORM6_P2']}

# ── Enum translation maps ─────────────────────────────────────────────────────
INSP_TYPE_MAP = {
    'annual':             'שוטפת שנתית',
    'major':              'יסודית',
    'pressure':           'לחץ',
    'major_and_pressure': 'יסודית+לחץ',
}
EXT_TYPE_MAP = {
    'powder': 'אבקה',
    'halon':  'הלוקרבון',
    'water':  'מים',
    'foam':   'קצף',
    'co2':    'CO2',
}
SUPPRESS_TYPE_MAP = {
    'aerosol': 'אירוסול',
    'gas':     'גז',
}
PANEL_TYPE_MAP = {
    'zone':        'אזורית',
    'analog':      'אנלוגית',
    'addressable': 'כתובתית',
    'interactive': 'אינטראקטיבית',
}
WATER_SOURCE_MAP = {
    'pumps':        'מערכת משאבות',
    'municipality': 'רשות המים',
}
YN_MAP = {  # enum: present/absent/na
    'present': 'V',
    'absent':  'X',
    'na':      '---',
}
ROUTE_MAP = {
    'police160': 'מפרט משטרה 160',
    'ti1220':    'ת"י 1220 חלק 3',
}


def _yn(val):
    """Boolean → תקין / לא תקין."""
    if val is None or val == '':
        return ''
    return 'תקין' if bool(val) else 'לא תקין'


def _check(val):
    """Boolean → ✓ / empty."""
    return '✓' if bool(val) else ''


def _safe_json(s, default=None):
    """Parse JSON string safely, return default on failure."""
    if default is None:
        default = []
    if not s:
        return default
    try:
        return json.loads(s)
    except Exception:
        return default


# ── Table definitions: page 2+ ───────────────────────────────────────────────
# Loaded from forms_config.json (FORM_TABLES). Column keys must match the
# normalized field names used in fill_table_page.
FORM_TABLES = {int(k): v for k, v in CFG['FORM_TABLES'].items()}


# ── Page builder ─────────────────────────────────────────────────────────────
def make_page(doc, form_num, pg_idx, w, h):
    """Add a page to doc and embed the background PNG."""
    page = doc.new_page(width=w, height=h)
    bg = os.path.join(BG_DIR, f'form{form_num}_page{pg_idx + 1}.png')
    if os.path.exists(bg):
        page.insert_image(fitz.Rect(0, 0, w, h), filename=bg)
    return page


# ── Page 1: header + klali + section ג ──────────────────────────────────────
def fill_page1(page, form_num, d):
    fn = form_num

    # Date
    dy = DATE_Y.get(fn)
    if dy and d.get('date'):
        ic(page, DATE_X[0], dy[0], DATE_X[1], dy[1], d['date'], fs=9, align='center')

    # Klali rows
    ky = KLALI_Y.get(fn)
    if ky:
        by0, by1 = ky['biz']
        ay0, ay1 = ky['addr']
        cy0, cy1 = ky['cont']

        ic_digits(page, FF_BOXES_X,  by0, by1, d.get('fire_file_number', ''))
        ic(page, BIZ_BN[0], by0, BIZ_BN[1], by1, d.get('business_name', ''))
        ic(page, BIZ_BT[0], by0, BIZ_BT[1], by1, d.get('business_type', ''))
        ic_digits(page, ID_BOXES_X,  by0, by1, d.get('vat_number', ''))

        ic(page, ADDR_CI[0], ay0, ADDR_CI[1], ay1, d.get('city', ''))
        ic(page, ADDR_ST[0], ay0, ADDR_ST[1], ay1, d.get('street', ''))
        ic(page, ADDR_HN[0], ay0, ADDR_HN[1], ay1, d.get('house_number', ''))
        ic(page, ADDR_ZP[0], ay0, ADDR_ZP[1], ay1, d.get('zip', ''))

        ic(page, CONT_CN[0], cy0, CONT_CN[1], cy1, d.get('contact_name', ''))
        ic(page, CONT_CR[0], cy0, CONT_CR[1], cy1, d.get('contact_role', ''))
        ic(page, CONT_CP[0], cy0, CONT_CP[1], cy1, d.get('contact_phone', ''))
        ic(page, CONT_CE[0], cy0, CONT_CE[1], cy1,
           d.get('contact_email', ''), fs=8, align='left')

    _section_gim(page, fn, d)


def _section_gim(page, fn, d):
    """Fill form-specific bottom fields (section ג / inspector / technician).

    Coordinates come from SECTION_GIM[fn][field_id] (config); the mapping of
    data value → field and any value formatting stays here.
    """
    S = SECTION_GIM.get(fn, {})

    if fn == 1:
        ic(page, *S['inspector_name'],    d.get('inspector_name', ''))
        ic(page, *S['business_name_sig'], d.get('business_name', ''))

    elif fn == 2:
        # Section א — inspector declaration
        ic(page, *S['inspector_name'], d.get('inspector_name', ''), fs=10, align='center')
        ic(page, *S['inspector_id'],   d.get('inspector_id', ''),   fs=10, align='center')
        # Section ב — inspection date
        ic(page, *S['date_decl'],      d.get('date', ''),           fs=10, align='center')
        # Section ג bottom
        ic(page, *S['inspector_name_b'], d.get('inspector_name', ''))
        ic(page, *S['business_name_sig'], d.get('business_name', ''))

    elif fn == 3:
        # Section א — electrician declaration
        ic(page, *S['inspector_name'], d.get('inspector_name', ''))
        ic(page, *S['inspector_id'],   d.get('inspector_id', ''))
        ic(page, *S['license_type'],   d.get('license_type', ''))
        ic(page, *S['license_number'], d.get('license_number', ''))
        ic(page, *S['date_decl'],      d.get('date', ''))

    elif fn == 4:
        # Form 4 page 1 — panel info section
        # These fields come from FireDetectionData (merged into common)
        ic(page, *S['date'],          d.get('date', ''))
        ic(page, *S['business_name'], d.get('business_name', ''))
        ic(page, *S['panel_type'],
           PANEL_TYPE_MAP.get(d.get('panel_type', ''), d.get('panel_type', '')))
        ic(page, *S['panel_model'],        d.get('panel_model', ''))
        ic(page, *S['panel_manufacturer'], d.get('panel_manufacturer', ''))
        ic(page, *S['compliance_check_date'], d.get('compliance_check_date', ''))
        # Risk level (I or II) checkbox area
        risk = d.get('risk_level', '')
        ic(page, *S['risk_level'], f'רמת סיכון {risk}' if risk else '')

    elif fn == 5:
        # Section ג — property holder
        ic(page, *S['property_holder_name'], d.get('property_holder_name', ''))
        ic(page, *S['property_address'],     d.get('property_address', ''))
        ic(page, *S['maintenance_company'],  d.get('maintenance_company', ''))
        ic(page, *S['maintenance_phone'],    d.get('maintenance_phone', ''))
        ic(page, *S['certification_number'], d.get('certification_number', ''))
        ic(page, *S['technician_name'],      d.get('technician_name', ''))
        ic(page, *S['technician_id'],        d.get('technician_id', ''))

    elif fn == 6:
        # Inspector fields (EmergencyAnnouncementData merged into common)
        ic(page, *S['inspector_name'], d.get('inspector_name', ''))
        ic(page, *S['inspector_id'],   d.get('inspector_id', ''))
        # Route / standard
        route_text = ROUTE_MAP.get(d.get('route', ''), d.get('route', ''))
        ic(page, *S['route'], route_text)

    elif fn == 7:
        # SprinklerData fields (all merged into common via render_form)
        # Section א — property holder
        ic(page, *S['property_holder_name'], d.get('property_holder_name', ''))
        ic(page, *S['property_holder_id'],   d.get('property_holder_id', ''))
        # Section ב — property address
        ic(page, *S['property_address'], d.get('property_address', ''))
        # Section ג — maintenance company
        ic(page, *S['company_name'], d.get('company_name', ''))
        # Section ד — tav teken + water source
        ic(page, *S['tav_teken_number'], d.get('tav_teken_number', ''))
        ws = WATER_SOURCE_MAP.get(d.get('water_source', ''), d.get('water_source', ''))
        ic(page, *S['water_source'], ws)
        # Section ה — technician
        ic(page, *S['technician_name'], d.get('technician_name', ''))
        # Pressure & conclusion
        ic(page, *S['pressure_low_psi'],  str(d.get('pressure_low_psi', '')))
        ic(page, *S['pressure_high_psi'], str(d.get('pressure_high_psi', '')))
        ic(page, *S['is_functional'], _yn(d.get('is_functional')))


# ── Page 2+: table rows (forms 1, 2, 3, 5) ───────────────────────────────────
def fill_table_page(page, form_num, rows, common):
    tc = FORM_TABLES.get(form_num)
    if not tc or 'columns' not in tc:
        return

    # Fire file number header
    fp = tc['fire_file_pos']
    ff = str(common.get('fire_file_number', ''))
    if ff:
        ic(page, fp['left'], fp['top'],
           fp['left'] + fp['width'], fp['top'] + fp['height'], ff)

    # Business name header (form 2)
    if form_num == 2 and 'biz_name_pos' in tc:
        bp = tc['biz_name_pos']
        ic(page, bp['left'], bp['top'],
           bp['left'] + bp['width'], bp['top'] + bp['height'],
           str(common.get('business_name', '')), align='right')

    # Table rows
    row_ys     = tc.get('row_y')
    row_start  = tc.get('row_start_y', 200)
    row_h      = tc.get('row_height', 14)

    for r_idx, row in enumerate(rows[:tc['max_rows']]):
        if row_ys:
            if r_idx + 1 >= len(row_ys):
                break
            y0 = row_ys[r_idx]
            y1 = row_ys[r_idx + 1]
        else:
            y0 = row_start + r_idx * row_h
            y1 = y0 + row_h

        rd = dict(row)

        # ── Normalize field names per form ──────────────────────────────────
        if form_num == 1:
            rd['num']     = str(rd.get('station_number', r_idx + 1))
            rd['hose']    = YN_MAP.get(rd.get('hose_2inch',         'na'), '')
            rd['nozzle']  = YN_MAP.get(rd.get('nozzle_2inch',       'na'), '')
            rd['cabinet'] = YN_MAP.get(rd.get('equipment_cabinet',  'na'), '')
            rd['reel']    = YN_MAP.get(rd.get('hose_reel',          'na'), '')

        elif form_num == 2:
            rd.setdefault('num', str(r_idx + 1))
            rd['id']           = rd.get('serial_number', '')
            rd['type']         = EXT_TYPE_MAP.get(rd.get('extinguisher_type', ''), rd.get('type', ''))
            rd['size_kg']      = str(rd.get('size_kg', ''))
            rd['next_major']   = rd.get('next_major_inspection', '')
            rd['next_pressure']= rd.get('next_pressure_test', '')
            rd['insp_type']    = INSP_TYPE_MAP.get(rd.get('inspection_type', ''), rd.get('insp_type', ''))
            func = rd.get('is_functional', True)
            rd['ok']     = '✓' if func     else ''
            rd['not_ok'] = '✓' if not func else ''

        elif form_num == 3:
            rd['num']        = str(rd.get('panel_number', r_idx + 1))
            rd['amperage']   = str(rd.get('amps', ''))
            rd['disconnect'] = _check(rd.get('has_disconnect'))
            rd['detection']  = _check(rd.get('has_detection'))
            rd['suppress']   = _check(rd.get('has_suppression'))

        elif form_num == 5:
            rd['num']      = str(rd.get('panel_number', r_idx + 1))
            rd['amperage'] = str(rd.get('amps', ''))
            rd['sup_type'] = SUPPRESS_TYPE_MAP.get(rd.get('suppression_type', ''), rd.get('suppression_type', ''))
            rd['weight']   = str(rd.get('suppression_weight_grams', ''))
            rd['status']   = _yn(rd.get('is_functional'))

        # Write each column
        for col in tc['columns']:
            val = rd.get(col['key'], '')
            if val:
                x0 = col['left']
                x1 = x0 + col['width']
                ic(page, x0, y0, x1, y1, str(val), fs=8, align='center')


# ── Form 4: special multi-page renderer ──────────────────────────────────────
def fill_form4_page(page, pg_idx, common, rows):
    """Render pages 2-4 of form 4 (FireDetectionData)."""
    tc = FORM_TABLES[4]
    fp = tc['fire_file_pos']
    ff = str(common.get('fire_file_number', ''))
    if ff:
        ic(page, fp['left'], fp['top'],
           fp['left'] + fp['width'], fp['top'] + fp['height'], ff)

    if not rows:
        return
    r = rows[0]

    if pg_idx == 1:
        # Page 2: detector table (from detectors_json)
        detectors = _safe_json(r.get('detectors_json', ''), [])
        cols = tc['detector_cols']
        y0_base = tc['detector_start_y']
        rh      = tc['detector_row_h']
        for i, det in enumerate(detectors[:tc['detector_max']]):
            y0 = y0_base + i * rh
            y1 = y0 + rh
            d = det if isinstance(det, dict) else {}
            row_data = {
                'det_num':      str(i + 1),
                'det_location': d.get('location', ''),
                'det_type':     d.get('type', ''),
                'det_zone':     str(d.get('zone', '')),
                'det_status':   _yn(d.get('is_functional')),
            }
            for col in cols:
                val = row_data.get(col['key'], '')
                if val:
                    ic(page, col['left'], y0, col['left'] + col['width'], y1,
                                         val, fs=8, align='center')

    elif pg_idx == 2:
        # Page 3: dialer phones + compliance info
        phones = _safe_json(r.get('dialer_phones_json', ''), [])
        cols   = tc['phone_cols']
        y0_base = tc['phone_start_y']
        rh      = tc['phone_row_h']
        for i, ph in enumerate(phones[:tc['phone_max']]):
            y0 = y0_base + i * rh
            y1 = y0 + rh
            d = ph if isinstance(ph, dict) else {'number': str(ph)}
            row_data = {
                'ph_num':    str(i + 1),
                'ph_number': d.get('number', str(ph)),
                'ph_note':   d.get('note', ''),
            }
            for col in cols:
                val = row_data.get(col['key'], '')
                if val:
                    ic(page, col['left'], y0, col['left'] + col['width'], y1,
                       val, fs=8, align='center')
        compliance = r.get('compliance_option', '')
        if compliance:
            ic(page, 200, 600, 500, 614, f'אפשרות {compliance.upper()}', fs=9)
        conclusion = r.get('conclusion', '')
        concl_text = 'תקינה' if conclusion == 'ok' else ('לא תקינה' if conclusion == 'not_ok' else '')
        if concl_text:
            ic(page, 200, 630, 500, 643, concl_text, fs=10)

    elif pg_idx == 3:
        # Page 4: defects list
        defects = _safe_json(r.get('defects_json', ''), [])
        cols    = tc['defect_cols']
        y0_base = tc['defect_start_y']
        rh      = tc['defect_row_h']
        for i, defect in enumerate(defects[:tc['defect_max']]):
            y0 = y0_base + i * rh
            y1 = y0 + rh
            desc = defect if isinstance(defect, str) else defect.get('description', str(defect))
            row_data = {
                'def_num':  str(i + 1),
                'def_desc': desc,
            }
            for col in cols:
                val = row_data.get(col['key'], '')
                if val:
                    ic(page, col['left'], y0, col['left'] + col['width'], y1,
                       val, fs=8, align='right' if col['key'] == 'def_desc' else 'center')


def fill_form6_page2(page, common):
    tc = FORM_TABLES[6]
    fp = tc['fire_file_pos']
    ff = str(common.get('fire_file_number', ''))
    if ff:
        ic(page, fp['left'], fp['top'],
           fp['left'] + fp['width'], fp['top'] + fp['height'], ff)
    # Inline declaration fields (form 6 page 2). Coordinates from FORM6_P2 config.
    ic(page, *FORM6_P2['inspector_name'],  common.get('inspector_name', ''), align='right')
    ic(page, *FORM6_P2['license_number'],  common.get('license_number', ''), align='right')
    ic(page, *FORM6_P2['license_expiry'],  common.get('license_expiry', ''), align='center')
    ic(page, *FORM6_P2['inspection_date'], common.get('inspection_date', ''), align='center')
    ic(page, *FORM6_P2['tav_teken_number'], common.get('tav_teken_number', ''), align='right')
    ic(page, *FORM6_P2['tav_teken_expiry'], common.get('tav_teken_expiry', ''), align='center')
    # Conclusion: mark תקינה or לא תקינה
    is_ok = common.get('is_functional', True)
    ic(page, *FORM6_P2['conclusion_ok'],  'תקינה' if is_ok else '', fs=10, align='center')
    ic(page, *FORM6_P2['conclusion_not'], '' if is_ok else 'לא תקינה', fs=10, align='center')
    # Signature area (bottom)
    ic(page, *FORM6_P2['inspector_name_sig'], common.get('inspector_name', ''))
    ic(page, *FORM6_P2['inspector_id_sig'],   common.get('inspector_id', ''))


def _maybe_append_checklist(form_num, data, pdf_bytes):
    # צ'קליסט מתזים (נלווה לטופס 7) — מצורף אחרי עמודי הטופס אם נשלח מה-CRM.
    # כשל בצ'קליסט לעולם לא מפיל את הפקת הטופס עצמו.
    try:
        chk = (data or {}).get('checklist')
        if int(form_num) == 7 and chk:
            import checklist_render
            return checklist_render.append_checklist(pdf_bytes, chk)
    except Exception as e:
        print('checklist append failed:', e)
    return pdf_bytes


def render_form(form_num, data):
    # Hybrid routing: if a per-form calibration exists (new generic system),
    # delegate to render_v2. Otherwise fall back to the legacy logic below.
    _cal = os.path.join(BASE_DIR, 'calibrations', f'form{form_num}.json')
    if os.path.exists(_cal):
        import render_v2
        return render_v2.render_form(form_num, data)
    common = dict(data.get('common', {}))
    rows   = data.get('rows', [])
    if form_num in (4, 6, 7) and rows:
        merged = dict(rows[0])
        merged.update(common)
        common = merged
    pages = FORM_PAGES.get(form_num)
    if not pages:
        raise ValueError(f'Unknown form_num: {form_num}')
    doc = fitz.open()
    for pg_idx, (pw, ph) in enumerate(pages):
        page = make_page(doc, form_num, pg_idx, pw, ph)
        if pg_idx == 0:
            fill_page1(page, form_num, common)
        elif form_num == 4:
            fill_form4_page(page, pg_idx, common, rows)
        elif form_num == 6:
            fill_form6_page2(page, common)
        else:
            fill_table_page(page, form_num, rows, common)
    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True, deflate_images=True,
             deflate_fonts=True, clean=True)
    return buf.getvalue()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': 'v4',
                    'forms': list(FORM_PAGES.keys())})


@app.route('/page-image', methods=['POST'])
def page_image_endpoint():
    """
    המרת עמוד PDF לתמונת JPEG — משמש את ייבוא הסריקות ב-CRM:
    יישור סריקות מסובבות + רזולוציה גבוהה לפני שליחה ל-Claude.
    קלט:  { pdf_url | pdf_base64, page (1-based, ברירת מחדל 1),
            rotate (0/90/180/270), dpi (ברירת מחדל 200, מקס 300) }
    פלט:  { jpg_base64, width, height, page_count }
    """
    try:
        payload = request.get_json(force=True)
        page_no = int(payload.get('page', 1))
        rotate = int(payload.get('rotate', 0)) % 360
        dpi = min(max(int(payload.get('dpi', 200)), 72), 300)
        if payload.get('pdf_base64'):
            data = base64.b64decode(payload['pdf_base64'])
        else:
            import urllib.request
            req = urllib.request.Request(payload['pdf_url'],
                                         headers={'User-Agent': 'avuka-renderer'})
            data = urllib.request.urlopen(req, timeout=60).read()
        doc = fitz.open('pdf', data)
        idx = min(max(page_no - 1, 0), doc.page_count - 1)
        page = doc[idx]
        # קנה מידה לפי dpi, אך תוחם את הצלע הארוכה — סריקות ענקיות ב-dpi גבוה
        # מייצרות pixmap של מאות MB ומפוצצות את זיכרון ה-512MB. 2200px מספיקים ל-OCR.
        MAX_SIDE = 2200
        scale = dpi / 72.0
        longest = max(page.rect.width, page.rect.height) * scale
        if longest > MAX_SIDE:
            scale *= MAX_SIDE / longest
        m = fitz.Matrix(scale, scale)
        if rotate:
            m.prerotate(rotate)
        pix = page.get_pixmap(matrix=m)
        jpg = pix.tobytes('jpeg', jpg_quality=82)
        w, h, pc = pix.width, pix.height, doc.page_count
        pix = None
        doc.close()
        import gc
        gc.collect()
        return jsonify({'jpg_base64': base64.b64encode(jpg).decode(),
                        'width': w, 'height': h,
                        'page_count': pc})
    except Exception:
        return jsonify({'error': traceback.format_exc()}), 500


@app.route('/render', methods=['POST'])
def render_endpoint():
    try:
        payload  = request.get_json(force=True)
        form_num = int(payload.get('form_num', 0))
        data     = payload.get('data', {})
        if form_num not in FORM_PAGES:
            return jsonify({'error': f'form_num {form_num} not supported'}), 400
        pdf_bytes = render_form(form_num, data)
        pdf_bytes = _maybe_append_checklist(form_num, data, pdf_bytes)
        pdf_b64   = base64.b64encode(pdf_bytes).decode()
        raw_name  = data.get('common', {}).get('business_name', 'form')
        name      = re.sub(r'[^\w\-]', '_', raw_name, flags=re.ASCII)
        name      = re.sub(r'_+', '_', name).strip('_') or 'form'
        filename  = f'avuka_form{form_num}_{name}.pdf'
        return jsonify({'pdf_base64': pdf_b64, 'filename': filename})
    except Exception:
        return jsonify({'error': traceback.format_exc()}), 500


@app.route('/merge', methods=['POST'])
def merge_endpoint():
    """
    POST /merge  →  { forms: [{form_num, data: {common, rows}}],
                      business_name?, date? }
                 →  { pdf_base64, filename }

    Renders each form individually (using render_form) and merges them into
    a single PDF.  Forms are sorted by form_num (1→7) regardless of the order
    in which they arrive, so the caller does not need to pre-sort.

    RTL quality and font rendering are identical to /render — we are simply
    appending pages from separate PyMuPDF documents with insert_pdf(), which
    is a lossless page-copy that preserves all embedded fonts and graphics.
    """
    try:
        payload = request.get_json(force=True)
        forms   = payload.get('forms', [])
        if not forms:
            return jsonify({'error': 'No forms provided'}), 400

        # Sort by form_num 1→7 before rendering
        forms_sorted = sorted(forms, key=lambda x: int(x.get('form_num', 0)))

        merged = fitz.open()
        for item in forms_sorted:
            form_num = int(item.get('form_num', 0))
            data     = item.get('data', {})
            if form_num not in FORM_PAGES:
                return jsonify({'error': f'form_num {form_num} not supported'}), 400
            pdf_bytes = render_form(form_num, data)
            pdf_bytes = _maybe_append_checklist(form_num, data, pdf_bytes)
            src = fitz.open('pdf', pdf_bytes)
            merged.insert_pdf(src)
            src.close()

        buf = io.BytesIO()
        merged.save(buf, garbage=4, deflate=True, deflate_images=True,
                    deflate_fonts=True, clean=True)
        pdf_b64 = base64.b64encode(buf.getvalue()).decode()

        raw_name = payload.get('business_name',
                               forms_sorted[0].get('data', {})
                               .get('common', {}).get('business_name', 'avuka'))
        date_str = payload.get('date', '')
        name = re.sub(r'[^\w\-]', '_', raw_name, flags=re.ASCII)
        name = re.sub(r'_+', '_', name).strip('_') or 'avuka'
        filename = (f'{name}_אישור_מרוכז_{date_str}.pdf'
                    if date_str else f'{name}_אישור_מרוכז.pdf')

        return jsonify({'pdf_base64': pdf_b64, 'filename': filename})
    except Exception:
        return jsonify({'error': traceback.format_exc()}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
