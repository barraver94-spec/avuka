"""
checklist_render.py — צ'קליסט מתזים (נלווה לטופס 7) בפורמט המותג של אבוקה.

מיישם את תבנית העיצוב "טופס בדיקת מתזים - אבוקה.html" (07/07/2026):
לוגו + כותרת עם קו אדום, פס פרטי טופס, כותרות חלקים (צ'יפ אדום + קו שחור),
שדות עם קו תחתון, טבלאות 5 עמודות עם עיגולי סימון, סיכום וחתימות, פוטר ממותג.

קלט: מבנה ה-checklist מ-generateFormPdf (buildSprinklerChecklistPayload),
כולל `record` (שדות חלק א גולמיים) ו-`ref` (פס פרטי הטופס).

append_checklist(pdf_bytes, chk) — מוסיף את עמודי הצ'קליסט אחרי עמודי טופס 7.
הפריסה זורמת (cursor-y) עם שבירת עמודים אוטומטית — אין צורך בכיול.
"""
import io, os, base64
import fitz
from bidi.algorithm import get_display

BASE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE, "assets", "avuka_logo.png")

# ---- טיפוגרפיה (Heebo/Rubik שחולצו מתבנית העיצוב; fallback ל-DejaVu) ----
def _font_path(*names):
    for n in names:
        p = os.path.join(BASE, "fonts", n)
        if os.path.exists(p):
            return p
    return os.path.join(BASE, "fonts", "DejaVuSans.ttf")

F_BODY  = _font_path("heebo.ttf")
F_BOLD  = _font_path("heebo-bold.ttf")
F_DISPB = _font_path("rubik-bold.ttf")
F_DISPK = _font_path("rubik-black.ttf")
F_MONO  = _font_path("plexmono.ttf")

FONTS = {"heb": F_BODY, "hb": F_BOLD, "rb": F_DISPB, "rk": F_DISPK, "mono": F_MONO}
_F = {k: fitz.Font(fontfile=v) for k, v in FONTS.items()}

# ---- צבעי המותג (מתוך ה-CSS של התבנית) ----
def _hex(c):
    return tuple(int(c[i:i+2], 16) / 255.0 for i in (1, 3, 5))

BRAND   = _hex('#E00101')
INK900  = _hex('#111113')
INK800  = _hex('#1C1C20')
INK500  = _hex('#565660')
INK400  = _hex('#767680')
INK300  = _hex('#9A9AA3')
BORDER  = _hex('#DBDBE0')   # ink-150
INK50   = _hex('#F4F4F6')
WHITE   = (1, 1, 1)

# ---- עמוד (A4, שוליים 13mm כמו בתבנית) ----
PAGE_W, PAGE_H = 595.32, 841.92
MARGIN = 36.9
TOP = MARGIN
BOTTOM = MARGIN + 18   # מקום לפוטר
CONTENT_W = PAGE_W - 2 * MARGIN
XR = PAGE_W - MARGIN   # קצה ימין
XL = MARGIN            # קצה שמאל

# עמודות טבלת הסעיפים (RTL: מס' ימני, לא-ישים שמאלי)
W_NUM, W_YES, W_NO, W_NA = 34, 39, 39, 46
X_NUM_L = XR - W_NUM
W_LABEL = CONTENT_W - W_NUM - W_YES - W_NO - W_NA
X_LBL_L = X_NUM_L - W_LABEL
X_YES_L = X_LBL_L - W_YES
X_NO_L  = X_YES_L - W_NO
X_NA_L  = X_NO_L - W_NA


def _is_ascii(s):
    try:
        str(s).encode('ascii'); return True
    except Exception:
        return False


def _w(font, s, fs):
    return _F[font].text_length(get_display(str(s)), fontsize=fs)


def _wrap(text, font, fs, maxw):
    """גלישת שורות בסדר לוגי; bidi פר שורה."""
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if not cur or _F[font].text_length(get_display(t), fontsize=fs) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return [get_display(l) for l in lines]


class Ctx:
    def __init__(self, doc):
        self.doc = doc
        self.page = None
        self.y = TOP
        self.n = 0

    def new_page(self):
        self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        for name, path in FONTS.items():
            self.page.insert_font(fontname=name, fontfile=path)
        self.n += 1
        self.y = TOP
        _footer(self)

    def ensure(self, h):
        if self.page is None or self.y + h > PAGE_H - BOTTOM:
            self.new_page()


def _text(ctx, x, y, s, font="heb", fs=9.75, color=INK900, anchor="r", maxw=None):
    """anchor: r=ימין(x=קצה ימני) l=שמאל c=מרכז. מכווץ עדין אם חורג מ-maxw."""
    disp = get_display(str(s))
    if font == "mono" and not _is_ascii(s):
        font = "heb"
    w = _F[font].text_length(disp, fontsize=fs)
    if maxw and w > maxw:
        while fs > 5 and _F[font].text_length(disp, fontsize=fs) > maxw:
            fs -= 0.25
        w = _F[font].text_length(disp, fontsize=fs)
    px = x - w if anchor == "r" else (x - w / 2.0 if anchor == "c" else x)
    ctx.page.insert_text((px, y), disp, fontsize=fs, fontname=font, color=color)
    return w


def _footer(ctx):
    y = PAGE_H - 22
    ctx.page.draw_line((XL, y - 8), (XR, y - 8), color=BORDER, width=0.7)
    _text(ctx, XR, y, 'ר. אבוקה (1993) בע"מ · ציוד ומערכות לגילוי וכיבוי אש · היתר מס\' 37801', "heb", 7.3, INK400)
    _text(ctx, XL, y, '04-8212912 · דרך בר יהודה 113, נשר', "heb", 7.3, INK400, anchor="l")
    _text(ctx, XL + CONTENT_W / 2.0, y + 11, f'עמוד {ctx.n}', "heb", 6.5, INK300, anchor="c")


def _rrect(ctx, rect, fill=None, color=None, width=0.75, radius=0.10):
    try:
        ctx.page.draw_rect(rect, color=color, fill=fill, width=width, radius=radius)
    except Exception:
        ctx.page.draw_rect(rect, color=color, fill=fill, width=width)


def _radio(ctx, cx, cy, selected, r=3.8):
    if selected:
        ctx.page.draw_circle((cx, cy), r, color=BRAND, fill=BRAND, width=0.8)
        ctx.page.draw_circle((cx, cy), r * 0.42, color=WHITE, fill=WHITE, width=0.4)
    else:
        ctx.page.draw_circle((cx, cy), r, color=INK300, width=0.9)


def _checkbox(ctx, x_left, cy, selected, size=8.2, label=None, fs=9.2, font="heb", color=INK800):
    """ריבוע סימון + תווית מימין לו (RTL: התווית משמאל לריבוע? בתבנית: ריבוע ואז טקסט)."""
    r = fitz.Rect(x_left, cy - size / 2, x_left + size, cy + size / 2)
    if selected:
        _rrect(ctx, r, fill=BRAND, color=BRAND, width=0.7, radius=0.18)
        # וי לבן
        p1 = (x_left + size * 0.22, cy + size * 0.02)
        p2 = (x_left + size * 0.42, cy + size * 0.24)
        p3 = (x_left + size * 0.80, cy - size * 0.26)
        ctx.page.draw_line(p1, p2, color=WHITE, width=1.1)
        ctx.page.draw_line(p2, p3, color=WHITE, width=1.1)
    else:
        _rrect(ctx, r, color=INK300, width=0.9, radius=0.18)


# ============================ בלוקים עיצוביים ============================

def _doc_header(ctx, chk):
    """כותרת עמוד 1: כותרת+תת-כותרת מימין, לוגו משמאל, קו אדום."""
    title = chk.get('title') or 'בחינה, בדיקה ותחזוקה של מערכת מתזים "רטובה" לכיבוי אש במים'
    sub = 'נספח בדיקה לאישור טופס 7 · בהתאם לתקן ישראלי ת"י 1928 — מערכות לכיבוי אש במים: בקרה, בדיקה ותחזוקה'
    logo_w = 0
    logo_h = 42
    if os.path.exists(LOGO):
        pix = fitz.Pixmap(LOGO)
        logo_w = logo_h * pix.width / pix.height
    title_w = CONTENT_W - logo_w - 18
    lines = _wrap(title, "rk", 15.5, title_w)
    y = ctx.y + 4
    ty = y + 14
    for l in lines:
        w = _F["rk"].text_length(l, fontsize=15.5)
        ctx.page.insert_text((XR - w, ty), l, fontsize=15.5, fontname="rk", color=INK900)
        ty += 19
    for l in _wrap(sub, "heb", 8.6, title_w):
        w = _F["heb"].text_length(l, fontsize=8.6)
        ctx.page.insert_text((XR - w, ty), l, fontsize=8.6, fontname="heb", color=INK500)
        ty += 11.5
    if logo_w:
        ctx.page.insert_image(fitz.Rect(XL, y, XL + logo_w, y + logo_h), filename=LOGO, keep_proportion=True)
    ctx.y = max(ty - 6, y + logo_h + 6) + 6
    ctx.page.draw_line((XL, ctx.y), (XR, ctx.y), color=BRAND, width=2.2)
    ctx.y += 12


def _ref_strip(ctx, chk):
    ref = chk.get('ref') or {}
    cells = [
        ("מס' טופס", ref.get('num') or '', 1.0),
        ("תאריך ביצוע", ref.get('date') or '', 1.0),
        ("שם הנכס / עסק", ref.get('site') or '', 1.4),
    ]
    h = 30
    ctx.ensure(h + 6)
    total = sum(c[2] for c in cells)
    r = fitz.Rect(XL, ctx.y, XR, ctx.y + h)
    _rrect(ctx, r, color=BORDER, width=0.9, radius=0.14)
    x_right = XR
    for i, (cap, val, flex) in enumerate(cells):
        w = CONTENT_W * flex / total
        if i:
            ctx.page.draw_line((x_right, ctx.y), (x_right, ctx.y + h), color=BORDER, width=0.8)
        _text(ctx, x_right - 10, ctx.y + 11, cap, "hb", 7.4, INK400)
        _text(ctx, x_right - 10, ctx.y + 23.5, val or '—', "mono" if _is_ascii(val) else "hb", 10, INK900, maxw=w - 20)
        x_right -= w
    ctx.y += h + 8


def _section_bar(ctx, chip, title):
    ctx.ensure(34)
    ctx.y += 12
    base = ctx.y + 12
    w1 = _text(ctx, XR, base, chip, "rk", 12, BRAND)
    _text(ctx, XR - w1 - 9, base, title, "rb", 11, INK900, maxw=CONTENT_W - w1 - 12)
    ctx.y = base + 5
    ctx.page.draw_line((XL, ctx.y), (XR, ctx.y), color=INK900, width=1.4)
    ctx.y += 9


def _sub_header(ctx, text):
    ctx.ensure(22)
    ctx.y += 8
    _text(ctx, XR, ctx.y + 10, text, "rb", 10.3, BRAND)
    ctx.y += 16


def _field(ctx, x_right, w, label, value):
    """שדה בסגנון התבנית: תווית קטנה, ערך, קו תחתון."""
    y = ctx.y
    _text(ctx, x_right, y + 8, label, "hb", 7.6, INK400, maxw=w)
    font = "mono" if (_is_ascii(value) and value) else "heb"
    _text(ctx, x_right - 1, y + 21, value or '', font, 9.8, INK900, maxw=w - 2)
    ctx.page.draw_line((x_right - w, y + 24.5), (x_right, y + 24.5), color=INK300, width=0.7)


def _fields_row(ctx, cells, gap=14):
    """cells: [(label, value, flex)] מימין לשמאל."""
    ctx.ensure(32)
    total = sum(c[2] for c in cells)
    avail = CONTENT_W - gap * (len(cells) - 1)
    x_right = XR
    for label, value, flex in cells:
        w = avail * flex / total
        _field(ctx, x_right, w, label, value)
        x_right -= w + gap
    ctx.y += 32


def _options_box(ctx, rows):
    """תיבת 'סמנו אפשרות אחת לפחות בכל שורה' — שורות עם ריבועי סימון."""
    head_h, row_h = 18, 22
    h = head_h + row_h * len(rows)
    ctx.ensure(h + 4)
    y0 = ctx.y
    _rrect(ctx, fitz.Rect(XL, y0, XR, y0 + h), color=BORDER, width=0.9, radius=0.05)
    ctx.page.draw_rect(fitz.Rect(XL, y0, XR, y0 + head_h), fill=INK50, color=None)
    ctx.page.draw_line((XL, y0 + head_h), (XR, y0 + head_h), color=BORDER, width=0.7)
    _text(ctx, XR - 10, y0 + 12.5, 'סמנו אפשרות אחת לפחות בכל שורה', "hb", 8.2, INK500)
    label_w = 160
    y = y0 + head_h
    for label, options, selected in rows:
        cy = y + row_h / 2.0
        _text(ctx, XR - 10, cy + 3.2, label, "heb", 9.2, INK800, maxw=label_w - 14)
        ctx.page.draw_line((XR - label_w, y), (XR - label_w, y + row_h), color=BORDER, width=0.7)
        x = XR - label_w - 16
        for opt in options:
            tw = _w("heb", opt, 9.2)
            _checkbox(ctx, x - 8.2, cy, opt == selected)
            _text(ctx, x - 12, cy + 3.2, opt, "heb", 9.2, INK800)
            x -= (8.2 + 6 + tw + 20)
        if (label, options, selected) != rows[-1]:
            ctx.page.draw_line((XL, y + row_h), (XR, y + row_h), color=BORDER, width=0.7)
        y += row_h
    ctx.y = y0 + h + 6


# ---------------- טבלת סעיפים (חלקים ב/ג/ד + הצהרות) ----------------

def _tbl_header(ctx, with_na=True, with_num=True):
    h = 17
    ctx.ensure(h)
    y = ctx.y
    ctx.page.draw_rect(fitz.Rect(XL, y, XR, y + h), fill=INK50, color=None)
    label_right = X_NUM_L if with_num else XR
    _text(ctx, label_right - 8, y + 11.7, 'סעיף', "hb", 8.2, INK500)
    _text(ctx, X_LBL_L - W_YES / 2.0, y + 11.7, 'כן', "hb", 8.2, INK500, anchor="c")
    _text(ctx, X_YES_L - W_NO / 2.0, y + 11.7, 'לא', "hb", 8.2, INK500, anchor="c")
    if with_na:
        _text(ctx, X_NO_L - W_NA / 2.0, y + 11.7, 'לא ישים', "hb", 8.2, INK500, anchor="c")
    ctx.page.draw_line((XL, y + h), (XR, y + h), color=BORDER, width=0.8)
    ctx.y += h


def _group_row(ctx, title, note=""):
    fs = 9.6
    note_lines = _wrap(note, "heb", 7.4, CONTENT_W - 20) if note else []
    h = 19 + len(note_lines) * 9.5
    if ctx.y + h + 30 > PAGE_H - BOTTOM:   # לא משאירים כותרת קבוצה יתומה
        ctx.new_page()
        _tbl_header(ctx)
    y = ctx.y
    ctx.page.draw_rect(fitz.Rect(XL, y, XR, y + h), fill=INK50, color=None)
    _text(ctx, XR - 9, y + 13, title, "hb", fs, INK900)
    ny = y + 13
    for l in note_lines:
        ny += 9.5
        w = _F["heb"].text_length(l, fontsize=7.4)
        ctx.page.insert_text((XR - 9 - w, ny), l, fontsize=7.4, fontname="heb", color=INK500)
    ctx.page.draw_line((XL, y + h), (XR, y + h), color=BORDER, width=0.7)
    ctx.y += h


def _item_row(ctx, it):
    fs, lh = 9.2, 12.2
    label = it.get('label') or ''
    extra = []
    if it.get('sub'):
        subs = [s for s in str(it['sub']).split('; ') if s]
        extra.append(('subs', subs))
    if it.get('value_only'):
        label = f"{label}: "
    if it.get('note'):
        nl = it.get('note_label') or 'הערות'
        extra.append(('note', f"{nl}: {it['note']}"))

    if it.get('header'):
        ctx.ensure(18)
        y = ctx.y
        _text(ctx, XR - 9, y + 12.5, (f"{it.get('num')} " if it.get('num') else '') + label, "hb", 9.3, INK800, maxw=CONTENT_W - 18)
        ctx.page.draw_line((XL, y + 17), (XR, y + 17), color=BORDER, width=0.6)
        ctx.y += 17
        return

    lines = _wrap(label, "heb", fs, W_LABEL - 16) if label.strip() else []
    extra_h = 0
    for kind, val in extra:
        if kind == 'note':
            extra_h += 11
        else:
            extra_h += 12
    row_h = max(len(lines) * lh + extra_h + 7, 18)
    if ctx.y + row_h > PAGE_H - BOTTOM:
        ctx.new_page()
        _tbl_header(ctx)
    y = ctx.y
    # מס' סעיף
    if it.get('num'):
        _text(ctx, XR - 8, y + 12.3, it['num'], "mono", 8.4, INK400)
    # תוכן הסעיף
    ty = y + 12.3
    for l in lines:
        w = _F["heb"].text_length(l, fontsize=fs)
        ctx.page.insert_text((X_NUM_L - 8 - w, ty), l, fontsize=fs, fontname="heb", color=INK800)
        ty += lh
    # ערך inline (סעיפי PSI)
    if it.get('value_only'):
        val = it.get('value') or ''
        last_w = _F["heb"].text_length(lines[-1], fontsize=fs) if lines else 0
        vx = X_NUM_L - 8 - last_w - 6
        vy = ty - lh
        vw = max(_w("mono" if _is_ascii(val) else "heb", val or '    ', 9.2), 34)
        _text(ctx, vx, vy, val, "mono", 9.2, INK900, )
        ctx.page.draw_line((vx - vw - 4, vy + 2.6), (vx + 2, vy + 2.6), color=INK300, width=0.7)
    # תתי-סימונים והערות
    for kind, val in extra:
        if kind == 'subs':
            x = X_NUM_L - 10
            cy = ty - 3
            for s in val:
                tw = _w("heb", s, 8.6)
                _checkbox(ctx, x - 8.2, cy, True, size=7.4)
                _text(ctx, x - 12, cy + 3, s, "heb", 8.6, INK800)
                x -= (8.2 + 6 + tw + 16)
            ty += 12
        else:
            _text(ctx, X_NUM_L - 10, ty - 1, val, "heb", 8.2, INK500, maxw=W_LABEL - 20)
            ty += 11
    # עיגולי סימון
    col = it.get('col') or ''
    cy = y + row_h / 2.0
    _radio(ctx, X_LBL_L - W_YES / 2.0, cy, col == 'yes')
    _radio(ctx, X_YES_L - W_NO / 2.0, cy, col == 'no')
    _radio(ctx, X_NO_L - W_NA / 2.0, cy, col == 'na')
    # קווי עמודות + תחתית
    for x in (X_NUM_L, X_LBL_L, X_YES_L, X_NO_L):
        ctx.page.draw_line((x, y), (x, y + row_h), color=BORDER, width=0.55)
    ctx.page.draw_line((XL, y + row_h), (XR, y + row_h), color=BORDER, width=0.55)
    ctx.y += row_h


def _decl_table(ctx, declarations):
    """הצהרת בעלי המבנה — טבלת כן/לא."""
    h = 17
    ctx.ensure(h + 24)
    y = ctx.y
    ctx.page.draw_rect(fitz.Rect(XL, y, XR, y + h), fill=INK50, color=None)
    _text(ctx, XR - 8, y + 11.7, 'סעיף', "hb", 8.2, INK500)
    _text(ctx, X_LBL_L - W_YES / 2.0, y + 11.7, 'כן', "hb", 8.2, INK500, anchor="c")
    _text(ctx, X_YES_L - W_NO / 2.0, y + 11.7, 'לא', "hb", 8.2, INK500, anchor="c")
    ctx.page.draw_line((XL, y + h), (XR, y + h), color=BORDER, width=0.8)
    ctx.y += h
    for d in declarations:
        lines = _wrap(d.get('label') or '', "heb", 9.2, W_NUM + W_LABEL - 16)
        row_h = max(len(lines) * 12.2 + 7, 18)
        ctx.ensure(row_h)
        y = ctx.y
        ty = y + 12.3
        for l in lines:
            w = _F["heb"].text_length(l, fontsize=9.2)
            ctx.page.insert_text((XR - 9 - w, ty), l, fontsize=9.2, fontname="heb", color=INK800)
            ty += 12.2
        cy = y + row_h / 2.0
        v = d.get('value')
        _radio(ctx, X_LBL_L - W_YES / 2.0, cy, v == 'כן')
        _radio(ctx, X_YES_L - W_NO / 2.0, cy, v == 'לא')
        for x in (X_LBL_L, X_YES_L):
            ctx.page.draw_line((x, y), (x, y + row_h), color=BORDER, width=0.55)
        ctx.page.draw_line((XL, y + row_h), (XR, y + row_h), color=BORDER, width=0.55)
        ctx.y += row_h


def _inline_choice(ctx, label, options, selected, y_add=3.2):
    """שורת בחירה אופקית: תווית + אפשרויות עם ריבועים/עיגולים."""
    ctx.ensure(22)
    cy = ctx.y + 11
    w = _text(ctx, XR, cy + y_add, label, "hb", 9.2, INK800)
    x = XR - w - 18
    for opt in options:
        tw = _w("heb", opt, 9.2)
        _checkbox(ctx, x - 8.2, cy, opt == selected)
        _text(ctx, x - 12, cy + 3.2, opt, "heb", 9.2, INK800)
        x -= (8.2 + 6 + tw + 22)
    ctx.y += 22


def _sig_image(ctx, data_url, rect):
    try:
        b64 = data_url.split(',', 1)[1] if ',' in data_url else data_url
        ctx.page.insert_image(rect, stream=base64.b64decode(b64), keep_proportion=True)
        return True
    except Exception:
        return False


def _sig_line(ctx, x_right, w, caption, image=None, value_text=None, h=52):
    """בלוק חתימה: תמונה/ערך מעל קו + כיתוב מתחת. מצייר במיקום נתון (לא מזיז סמן)."""
    y0 = ctx.y
    line_y = y0 + h - 14
    if image:
        _sig_image(ctx, image, fitz.Rect(x_right - w + 6, y0 + 2, x_right - 6, line_y - 2))
    elif value_text:
        _text(ctx, x_right - w / 2.0, line_y - 6, value_text, "heb", 9.5, INK900, anchor="c", maxw=w - 8)
    ctx.page.draw_line((x_right - w, line_y), (x_right, line_y), color=INK800, width=0.8)
    _text(ctx, x_right - w / 2.0, line_y + 10.5, caption, "heb", 7.6, INK400, anchor="c", maxw=w)


# ============================ הרכבה ============================

def render_checklist(doc, chk):
    ctx = Ctx(doc)
    ctx.new_page()
    rec = chk.get('record') or {}

    _doc_header(ctx, chk)
    _ref_strip(ctx, chk)

    # ---- חלק א ----
    _section_bar(ctx, "חלק א'", 'פרטים כלליים')

    exam_sel = {'weekly': 'שבועית', 'monthly': 'חודשית', 'quarterly': 'רבעונית', 'yearly': 'שנתית'}.get(rec.get('exam_type'), '')
    test_sel = {'quarterly': 'רבעונית', 'half_yearly': 'חצי־שנתית', 'yearly': 'שנתית'}.get(rec.get('test_type'), '')
    maint_sel = {'routine': 'שוטפת', 'yearly': 'שנתית'}.get(rec.get('maint_type'), '')
    _options_box(ctx, [
        ("הבחינה המדווחת בטופס זה (חלק ב')", ['שבועית', 'חודשית', 'רבעונית', 'שנתית'], exam_sel),
        ("הבדיקה המדווחת בטופס זה (חלק ג')", ['רבעונית', 'חצי־שנתית', 'שנתית'], test_sel),
        ("התחזוקה המדווחת בטופס זה (חלק ד')", ['שוטפת', 'שנתית'], maint_sel),
    ])

    _sub_header(ctx, '1. פרטים על המבנה')
    _fields_row(ctx, [('שם המבנה', rec.get('building_name'), 1), ('שם הבעלים', rec.get('owner_name'), 1)])
    _fields_row(ctx, [('האזורים הנבדקים במבנה בבדיקה זאת', rec.get('inspected_areas'), 1)])
    _fields_row(ctx, [('יישוב', rec.get('city'), 1.2), ('רחוב', rec.get('street'), 1.4), ("מס' בית", rec.get('house_number'), 0.7),
                      ('גוש', rec.get('gush'), 0.8), ('חלקה', rec.get('helka'), 0.8), ('מגרש', rec.get('migrash'), 0.8)])
    _fields_row(ctx, [('איש קשר — שם', rec.get('contact_name'), 1.2), ('טלפון נייד', rec.get('contact_phone'), 0.9),
                      ('פקס', rec.get('contact_fax'), 0.9), ('כתובת דוא"ל', rec.get('contact_email'), 1.4)])

    _sub_header(ctx, '2. פרטים על מבצע הבחינה / הבדיקה / התחזוקה')
    _fields_row(ctx, [('החברה המבצעת', rec.get('company_name'), 1.6), ('מספר טלפון', rec.get('company_phone'), 1), ('מספר היתר', rec.get('company_permit'), 1)])
    _fields_row(ctx, [('כתובת החברה', rec.get('company_address'), 1)])
    _fields_row(ctx, [('שם פרטי המבצע', rec.get('performer_first_name'), 1), ('שם משפחה', rec.get('performer_last_name'), 1),
                      ('מספר טלפון', rec.get('performer_phone'), 1), ('תאריך ביצוע', rec.get('exec_date'), 0.8), ('שעת ביצוע', rec.get('exec_time'), 0.6)])
    _fields_row(ctx, [('שם נציג הבעלים / איש קשר שנכח בזמן הבדיקה', rec.get('present_rep_name'), 1), ('הערות / צירוף מסמכים נוספים', rec.get('notes'), 1)])

    _sub_header(ctx, '3. הצהרת בעלי המבנה')
    _decl_table(ctx, chk.get('declarations') or [])

    _sub_header(ctx, '4. פרטים על מערכת אספקת המים')
    ws = {'municipal': 'רשת עירונית', 'pumps': 'מערכת משאבות'}.get(rec.get('water_supply'), '')
    _inline_choice(ctx, 'מערכת אספקת המים:', ['רשת עירונית', 'מערכת משאבות'], ws)
    wr = {'yes': 'כן', 'no': 'לא'}.get(rec.get('water_maint_report_valid'), '')
    _inline_choice(ctx, 'האם קיים דו"ח תחזוקה בתוקף?', ['כן', 'לא'], wr)

    _sub_header(ctx, '5. הצהרת המבצע')
    for l in _wrap('אני מצהיר שהמידע שנמסר בטופס זה מלא, מדויק ונכון למועד ביצוע הבחינה / הבדיקה / התחזוקה, ושכל הציוד הושאר בתום הבדיקה במצב פעולה.', "heb", 9.2, CONTENT_W):
        ctx.ensure(13)
        w = _F["heb"].text_length(l, fontsize=9.2)
        ctx.page.insert_text((XR - w, ctx.y + 10), l, fontsize=9.2, fontname="heb", color=INK800)
        ctx.y += 12.5
    sigs = chk.get('signatures') or {}
    ctx.ensure(64)
    ctx.y += 6
    half = (CONTENT_W - 30) / 2.0
    _sig_line(ctx, XR, half, 'חתימת המבצע' + (f" — {sigs.get('performer_name')}" if sigs.get('performer_name') else ''), image=sigs.get('performer_image'))
    _sig_line(ctx, XR - half - 30, half, 'חותמת החברה')
    ctx.y += 62

    # ---- חלקים ב/ג/ד ----
    chips = ["חלק ב'", "חלק ג'", "חלק ד'"]
    for i, sec in enumerate(chk.get('sections') or []):
        title = (sec.get('title') or '')
        clean = title.split('–', 1)[1].strip() if '–' in title else title
        _section_bar(ctx, chips[i] if i < 3 else '', clean)
        if sec.get('floor_area'):
            _fields_row(ctx, [('שטח הרצפה', sec['floor_area'], 0.4), ('', '', 1.2)])
        _tbl_header(ctx)
        for g in (sec.get('groups') or []):
            _group_row(ctx, g.get('title') or '', g.get('note') or '')
            for it in (g.get('items') or []):
                _item_row(ctx, it)
        ctx.y += 6

    # ---- סיכום ----
    summary = chk.get('summary') or {}
    _section_bar(ctx, 'סיכום', 'תוצאות בדיקת מערכת המתזים')
    st = summary.get('status') or ''
    ctx.ensure(24)
    cy = ctx.y + 11
    x = XR
    for opt, val in [('המערכת תקינה', 'מערכת תקינה'), ('המערכת אינה תקינה', 'מערכת אינה תקינה')]:
        tw = _w("hb", opt, 10)
        _radio(ctx, x - 5, cy, st == val, r=4.4)
        _text(ctx, x - 13, cy + 3.5, opt, "hb", 10, INK900)
        x -= (tw + 46)
    ctx.y += 26

    _sub_header(ctx, 'פירוט הסיבות לסימון "לא" בסעיפי הטופס')
    reasons = list(summary.get('reasons') or [])
    while len(reasons) < 4:
        reasons.append({'section': '', 'reason': ''})
    # כותרת טבלת סיבות
    h = 17
    ctx.ensure(h + 20)
    y = ctx.y
    sec_w = 110
    ctx.page.draw_rect(fitz.Rect(XL, y, XR, y + h), fill=INK50, color=None)
    _text(ctx, XR - 8, y + 11.7, "מס' הסעיף", "hb", 8.2, INK500)
    _text(ctx, XR - sec_w - 8, y + 11.7, 'הסיבה לסימון "לא"', "hb", 8.2, INK500)
    ctx.page.draw_line((XL, y + h), (XR, y + h), color=BORDER, width=0.8)
    ctx.y += h
    for r in reasons:
        lines = _wrap(r.get('reason') or '', "heb", 9.2, CONTENT_W - sec_w - 20) or ['']
        row_h = max(len(lines) * 12.2 + 6.5, 17)
        ctx.ensure(row_h)
        y = ctx.y
        _text(ctx, XR - 8, y + 12, r.get('section') or '', "heb", 8.8, INK800, maxw=sec_w - 12)
        ty = y + 12
        for l in lines:
            w = _F["heb"].text_length(l, fontsize=9.2)
            ctx.page.insert_text((XR - sec_w - 8 - w, ty), l, fontsize=9.2, fontname="heb", color=INK800)
            ty += 12.2
        ctx.page.draw_line((XR - sec_w, y, ), (XR - sec_w, y + row_h), color=BORDER, width=0.55)
        ctx.page.draw_line((XL, y + row_h), (XR, y + row_h), color=BORDER, width=0.55)
        ctx.y += row_h

    _sub_header(ctx, 'אישור קבלת תוצאות הבדיקה')
    ctx.ensure(64)
    third = (CONTENT_W - 40) / 3.0
    _sig_line(ctx, XR, third, 'שם נציג הבעלים / איש קשר שנכח בזמן הבדיקה', value_text=sigs.get('rep_name') or '')
    _sig_line(ctx, XR - third - 20, third, 'חתימה', image=sigs.get('rep_image'))
    _sig_line(ctx, XR - 2 * (third + 20), third, 'תאריך ושעה', value_text=sigs.get('rep_time') or '')
    ctx.y += 62


def append_checklist(pdf_bytes, chk):
    """מוסיף עמודי צ'קליסט אחרי עמודי הטופס הקיימים ומחזיר PDF מאוחד."""
    doc = fitz.open('pdf', pdf_bytes)
    render_checklist(doc, chk)
    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue()
