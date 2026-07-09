"""
render_v2.py — Generic, config-driven Avuka fire-form renderer.
Places every field defined in calibrations/form{N}.json onto the form.
Supports type=image for signatures/stamps (base64 dataURL or http(s) URL).
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
    if text is None or str(text) == "":
        return
    html = (f'<p dir="rtl" style="font-family: Arial, sans-serif; '
            f'font-size: {fs}px; font-weight: normal; text-align: {align}; '
            f'margin: 0; padding: 0; line-height: {max(y1-y0,6)}px;">{text}</p>')
    page.insert_htmlbox(fitz.Rect(x0, y0, x1, y1), html)


_DJV = fitz.Font(fontfile=FONT)


def _wrap_rtl(text, fs, maxw):
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
    if text is None or str(text) == "":
        return
    raw = str(text)
    s = get_display(raw)
    w_cell = (x1 - x0) - 1.2
    h_cell = y1 - y0
    if _DJV.text_length(s, fontsize=fs) <= w_cell:
        voff = max(((y1 - y0) - fs) / 2.0 - 0.5, 0)
        page.insert_textbox(fitz.Rect(x0, y0 + voff, x1, y1 + 2), s, fontsize=fs,
                            fontname="djv", align=_ALIGN.get(align, 1))
        return
    f = fs
    while f > 5 and _DJV.text_length(s, fontsize=f) > w_cell:
        f -= 0.5
    if _DJV.text_length(s, fontsize=f) <= w_cell:
        lines, use = [s], f
    else:
        lines, use = None, None
        for cand in (5.5, 5.0, 4.5, 4.0):
            ls = _wrap_rtl(raw, cand, w_cell)
            if (all(_DJV.text_length(l, fontsize=cand) <= w_cell for l in ls)
                    and len(ls) * cand * 1.22 <= h_cell + 1.0):
                lines, use = ls, cand
                break
        if lines is None:
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
    """חתימה/חותמת מ-URL (חתימות טכנאי) או base64/dataURL (חתימות canvas).
    כשל בפענוח לעולם לא מפיל את הרינדור — פשוט מדלג."""
    if not value or not isinstance(value, str):
        return
    try:
        v = value.strip()
        if v.startswith("http://") or v.startswith("https://"):
            import urllib.request
            req = urllib.request.Request(v, headers={"User-Agent": "avuka-renderer"})
            raw = urllib.request.urlopen(req, timeout=25).read()
        else:
            b64 = v.split(",", 1)[1] if v.startswith("data:") else v
            raw = base64.b64decode(b64)
        top = y0 - pad_y if pad_y else min(y0, y1) - 14
        rect = fitz.Rect(min(x0, x1), top, max(x0, x1), max(y0, y1))
        page.insert_image(rect, stream=raw, keep_proportion=True, overlay=True)
    except Exception as e:
        print("signature image skipped:", str(e)[:120])


def _open_with_background(form_num, n_pages):
    blank = os.path.join(BASE, "blanks", f"form{form_num}.pdf")
    if os.path.exists(blank):
        return fitz.open(blank)
    doc = fitz.open()
    for i in range(n_pages):
        png = os.path.join(BG, f"form{form_num}_page{i+1}.png")
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
    tbl = cfg.get("table")
    table_pages = []
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
                doc.fullcopy_page(tp)
                table_pages.append(doc.page_count - 1)
    total_appendix = max(len(table_pages), 1)
    for _pidx in table_pages:
        doc[_pidx].insert_font(fontname="djv", fontfile=FONT)
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
                _put_image(page, f["x0"], f["y0"], f["x1"], f["y1"], v, f.get("pad_y", 0))
            else:
                _put(page, f["x0"], f["y0"], f["x1"], f["y1"], v, f.get("fs", 9), f.get("align", "center"))

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
