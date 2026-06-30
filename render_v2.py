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
import os, io, json, glob
import fitz

BASE = os.path.dirname(os.path.abspath(__file__))
CAL  = os.path.join(BASE, "calibrations")
BG   = os.path.join(BASE, "backgrounds")
PORTRAIT  = (595.32, 841.92)
LANDSCAPE = (841.92, 595.32)


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
    for f in cfg["fields"]:
        si = f.get("show_if")
        if si and not common.get(si):
            continue
        page = doc[f["page"]]
        v = common.get(f.get("data_key", f["id"]), "")
        t = f.get("type", "text")
        if t == "digits":
            s = str(v); bx = f["boxes_x"]
            for i in range(len(bx) - 1):
                if i < len(s):
                    _put(page, bx[i], f["y0"], bx[i+1], f["y1"], s[i], f.get("fs", 9), "center")
        elif t == "checkbox":
            if v:
                _put(page, f["x0"], f["y0"], f["x1"], f["y1"], "V", f.get("fs", 9), "center")
        else:
            _put(page, f["x0"], f["y0"], f["x1"], f["y1"], v, f.get("fs", 9), f.get("align", "center"))
    t = cfg.get("table")
    if t and rows and t.get("columns") and 0 <= t.get("page", 99) < doc.page_count:
        page = doc[t["page"]]; ry = t["row_y"]
        for i, row in enumerate(rows[:len(ry) - 1]):
            for c in t["columns"]:
                _put(page, c["x0"], ry[i], c["x1"], ry[i+1], row.get(c["key"], ""), 8, "center")
    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    return buf.getvalue()
