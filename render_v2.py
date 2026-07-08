"""
render_v2.py — Generic, config-driven Avuka fire-form renderer.

Replaces the hard-coded per-field logic of app.py with ONE generic renderer
that places every field defined in a calibration file:
    calibrations/form{N}.json   (produced by the visual calibrator)

Each field has an `id` (unique) and a `data_key` (the key looked up in the
incoming data). Multiple fields may share a data_key (e.g. the inspector
signature on pages 1 and 2 both read `inspector_name`). No per-field Python
code: add a field in the calibrator and it renders here automatically.

Background per page: a vector blank PDF from blanks/form{N}.pdf if present,
otherwise the PNG backgrounds in backgrounds/form{N}_page{M}.png (same assets
the current app.py uses).

NOT yet wired to production. This is the target for switching app.py over once
all 7 forms are calibrated.
"""
import os, io, json, glob, base64
import fitz
from bidi.algorithm import get_display

BASE = os.path.dirname(os.path.abspath(__file__))
CAL  = os.path.join(BASE, "calibrations")
BG   = os.path.join(BASE, "backgrounds")
PORTRAIT  = (595.32, 841.92)
LANDSCAPE = (841.92, 595.32)
FONT = os.path.join(BASE, "fonts", "DejaVuSans.ttf")
_ALIGN = {"center": 1, "left": 0, "right": 2}


def _put(page, x0, y0, x1, y1, text, fs=9, align="center"):
    # Same approach as the legacy app.py ic(): plain insert_htmlbox with
    # Arial/sans-serif. PyMuPDF resolves a Hebrew-capable fallback on the
    # server (proven by the legacy renderer). No custom font archive.
    if text is None or str(text) == "":
        return
    html = (f'<p dir="rtl" style="font-family: Arial, sans-serif; '
            f'font-size: {fs}px; font-weight: normal; text-align: {align}; '
            f'margin: 0; padding: 0; line-height: {max(y1-y0,6)}px;">{text}</p>')
    page.insert_htmlbox(fitz.Rect(x0, y0, x1, y1), html)


# Module-level Font for width measurement only (not embedded per call).
_DJV = fitz.Font(fontfile=FONT)


def _wrap_rtl(text, fs, maxw):
    """Split logical text into lines that fit maxw, then bidi-reorder each
    line separately. Wrapping must happen in LOGICAL order — wrapping the
    visual string would put the end of the sentence on the first line."""
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if not cur or _DJV.text_length(get_display(t), fontsize=fs) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return [get_display(l) for l in lines]


def _put_fast(page, x0, y0, x1, y1, text, fs=8, align="center"):
    # Fast Hebrew-aware cell text via insert_textbox (much faster than
    # insert_htmlbox). python-bidi reorders logical->visual for correct RTL.
    #
    # OVERFLOW FIX (06/07/2026): insert_textbox silently writes NOTHING when
    # the text is wider than the rect — long serials/locations/notes were
    # dropped from printed forms while present in the DB. Now: keep the
    # original path when the text fits at the requested size; otherwise
    # shrink the font, and if a single line still can't fit, word-wrap
    # (logical-order) onto up to the cell height. A value is never dropped.
    if text is None or str(text) == "":
        return
    raw = str(text)
    s = get_display(raw)
    w_cell = (x1 - x0) - 1.2
    h_cell = y1 - y0

    if _DJV.text_length(s, fontsize=fs) <= w_cell:
        # Fits at requested size — identical to the original behaviour.
        voff = max(((y1 - y0) - fs) / 2.0 - 0.5, 0)
        # Use the page-registered font (see insert_font in render_form).
        # Passing fontfile= on every call re-embeds the 757KB TTF thousands
        # of times and crashes the worker on large tables.
        page.insert_textbox(fitz.Rect(x0, y0 + voff, x1, y1 + 2), s, fontsize=fs,
                            fontname="djv", align=_ALIGN.get(align, 1))
        return

    # 1) Shrink a single line down to 5pt.
    f = fs
    while f > 5 and _DJV.text_length(s, fontsize=f) > w_cell:
        f -= 0.5
    if _DJV.text_length(s, fontsize=f) <= w_cell:
        lines, use = [s], f
    else:
        # 2) Word-wrap in logical order, largest size whose lines fit
        #    both the width and the cell height.
        lines, use = None, None
        for cand in (5.5, 5.0, 4.5, 4.0):
            ls = _wrap_rtl(raw, cand, w_cell)
            if (all(_DJV.text_length(l, fontsize=cand) <= w_cell for l in ls)
                    and len(ls) * cand * 1.22 <= h_cell + 1.0):
                lines, use = ls, cand
                break
        if lines is None:
            # 3) Last resort: 4pt, keep as many lines as fit — a squeezed
            #    value beats a silently missing one.
            use = 4.0
            max_lines = max(int((h_cell + 1.0) // (use * 1.22)), 1)
            lines = _wrap_rtl(raw, use, w_cell)[:max_lines]

    lh = use * 1.22
    ty = y0 + max((h_cell - lh * len(lines)) / 2.0, 0) + use
    for l in lines:
        lw = _DJV.text_length(l, fontsize=use)
        if align == "right":
            tx = max(x1 - 0.6 - lw, x0 + 0.6)
        elif align == "left":
            tx = x0 + 0.6
        else:
            tx = x0 + max((x1 - x0 - lw) / 2.0, 0.6)
        page.insert_text((tx, ty), l, fontsize=use, fontname="djv")
        ty += lh


def _put_image(page, x0, y0, x1, y1, value, pad_y=0):
    """מציב חתימה/חותמת מ-dataURL (או base64 גולמי) בתוך תיבה, בשמירת יחס.
    כשל בפענוח לעולם לא מפיל את הרינדור — פשוט מדלג."""
    if not value or not isinstance(value, str):
        return
    try:
        b64 = value.split(",", 1)[1] if value.startswith("data:") else value
        raw = base64.b64decode(b64)
        # התיבה בכיול היא שורת טקסט דקה; מרחיבים כלפי מעלה כדי לתת גובה לחתימה.
        top = y0 - pad_y if pad_y else min(y0, y1) - 14
        rect = fitz.Rect(min(x0, x1), top, max(x0, x1), max(y0, y1))
        page.insert_image(rect, stream=raw, keep_proportion=True, overlay=True)
    except Exception as e:
        print("signature image skipped:", str(e)[:120])


def _open_with_background(form_num, n_pages):
    """Return a doc with backgrounds. Prefer a vector blank PDF; else PNGs."""
    blank = os.path.join(BASE, "blanks", f"form{form_num}.pdf")
    if os.path.exists(blank):
        return fitz.open(blank)
    doc = fitz.open()
    for i in range(n_pages):
        png = os.path.join(BG, f"form{form_num}_page{i+1}.png")
        # page size: portrait unless the PNG is wider than tall
        w, h = PORTRAIT
        if os.path.exists(png):
            px = fitz.Pixmap(png)
            if px.width > px.height:
                w, h = LANDSCAPE
        page = doc.new_page(width=w, height=h)
        if os.path.exists(png):
            page.insert_image(fitz.Rect(0, 0, w, h), filename=png)
    return doc


def render_form(form_num, data, blank_pdf=None):
    cfg = json.load(open(os.path.join(CAL, f"form{form_num}.json"), encoding="utf-8"))
    common = (data or {}).get("common", {})
    rows   = (data or {}).get("rows", [])
    n_pages = 1 + max([f.get("page", 0) for f in cfg["fields"]] +
                      [cfg.get("table", {}).get("page", 0)])
    doc = fitz.open(blank_pdf) if blank_pdf else _open_with_background(form_num, n_pages)

    # --- Table pagination ---
    # Split table rows across as many copies of the appendix page as needed.
    # capacity per page = number of row slots = len(row_y) - 1
    tbl = cfg.get("table")
    table_pages = []   # page indices holding each table chunk, in order
    chunks = []
    appendix_page = tbl.get("page") if tbl else None
    if tbl and rows and tbl.get("columns"):
        ry = tbl["row_y"]
        cap = len(ry) - 1
        tp = tbl.get("page", 0)
        if cap > 0 and 0 <= tp < doc.page_count:
            chunks = [rows[i:i + cap] for i in range(0, len(rows), cap)]
            table_pages = [tp]
            for _ in range(1, len(chunks)):
                doc.fullcopy_page(tp)            # clean copy of the appendix page
                table_pages.append(doc.page_count - 1)
    total_appendix = max(len(table_pages), 1)

    # Register the Hebrew font on each appendix page for the fast table path
    for _pidx in table_pages:
        doc[_pidx].insert_font(fontname="djv", fontfile=FONT)

    # --- Fields (repeat appendix-page fields on every overflow page) ---
    for f in cfg["fields"]:
        si = f.get("show_if")
        if si and not common.get(si):
            continue
        targets = [f["page"]]
        if appendix_page is not None and f["page"] == appendix_page and table_pages:
            targets = list(table_pages)
        dkey = f.get("data_key", f["id"])
        ttype = f.get("type", "text")
        for pos, pidx in enumerate(targets):
            page = doc[pidx]
            if dkey == "p2_page_num":
                v = str(pos + 1)
            elif dkey == "p2_page_total":
                v = str(total_appendix)
            else:
                v = common.get(dkey, "")
            if ttype == "digits":
                s = str(v); bx = f["boxes_x"]
                for i in range(len(bx) - 1):
                    if i < len(s):
                        _put(page, bx[i], f["y0"], bx[i+1], f["y1"], s[i], f.get("fs", 9), "center")
            elif ttype == "checkbox":
                if v:
                    _put(page, f["x0"], f["y0"], f["x1"], f["y1"], "V", f.get("fs", 9), "center")
            elif ttype == "image":
                # חתימות/חותמת: ערך = data:image/...;base64,XXX (dataURL) או base64 גולמי.
                # מוצב בתוך התיבה בשמירת יחס. תיבה גבוהה מהשורה — pad_y מרחיב כלפי מעלה.
                _put_image(page, f["x0"], f["y0"], f["x1"], f["y1"], v, f.get("pad_y", 0))
            else:
                _put(page, f["x0"], f["y0"], f["x1"], f["y1"], v, f.get("fs", 9), f.get("align", "center"))

    # --- Table rows ---
    if chunks:
        ry = tbl["row_y"]
        for k, chunk in enumerate(chunks):
            page = doc[table_pages[k]]
            for i, row in enumerate(chunk):
                for c in tbl["columns"]:
                    _put_fast(page, c["x0"], ry[i], c["x1"], ry[i + 1], row.get(c["key"], ""), 8, "center")

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    return buf.getvalue()
