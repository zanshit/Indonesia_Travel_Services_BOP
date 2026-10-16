"""Position-based table reader for BPS PDFs with a text layer (pymupdf words).

Column geometry comes from the "(1) (2) (3) ..." marker row that BPS prints under every table header.
Numbers are assigned to the nearest marker column by x-centre; the label column is column (1).
Wrapped (multi-line) labels are attached to the numeric row whose y-band contains them.
"""
import re
import pymupdf

NUM_MARK = re.compile(r"^\((\d+)\)$")
NA_TOKENS = {"NA", "-", "–", "—", "�", "n.a.", "..", "...", "x", "X"}


def _lines(words, tol=2.5):
    """Group words into lines by y-centre."""
    ws = sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    out, cur, cy = [], [], None
    for w in ws:
        yc = (w[1] + w[3]) / 2
        if cy is None or abs(yc - cy) <= tol:
            cur.append(w); cy = yc if cy is None else (cy * (len(cur) - 1) + yc) / len(cur)
        else:
            out.append(cur); cur = [w]; cy = yc
    if cur:
        out.append(cur)
    return out


def looks_numeric(s):
    s = s.strip()
    if s in NA_TOKENS:
        return True
    return bool(re.fullmatch(r"-?\d{1,3}(\.\d{3})*(,\d+)?|-?\d+(\.\d+)?|-?\d+,\d+", s))


def read_table(page, anchors=("Negara Tujuan Utama", "Negara/Wilayah/Entitas", "Negara/Wilayah", "Tujuan Utama1/")):
    """Return dict(markers, headers, rows) or None if the page has no marker row."""
    words = [w for w in page.get_text("words") if (w[3] - w[1]) < 30]   # drop diagonal watermark words
    # drop running-footer lines (publication title + page number) near the bottom of the page
    H = page.rect.height
    foot = set()
    for ln in _lines(words):
        txt = " ".join(w[4] for w in ln)
        if (ln[0][1] > 0.85 * H and re.search(r"(Statistik (Wisatawan|Kunjungan|Pengeluaran)|International Visitor|Outbound Tourism Statistics)", txt)):
            foot.update(id(w) for w in ln)
    words = [w for w in words if id(w) not in foot]
    # marker row: >=2 words "(n)" on one line
    marks = None
    for ln in _lines(words):
        m = [w for w in ln if NUM_MARK.match(w[4])]
        if len(m) >= 2 and (marks is None or True):
            marks = sorted(m, key=lambda w: w[0])
            break
    if not marks:
        return None
    my0 = min(w[1] for w in marks)
    mids = [(w[0] + w[2]) / 2 for w in marks]
    colnum = [int(NUM_MARK.match(w[4]).group(1)) for w in marks]
    bound = (mids[0] + mids[1]) / 2          # x boundary between label col and data cols
    # header words: between anchor top and marker row
    top = None
    for w in words:
        if w[1] < my0 and (w[0] + w[2]) / 2 <= bound and w[4].startswith(("Negara", "Jenis", "Maksud", "Pintu", "Bulan", "Kebangsaan", "KEBANGSAAN", "NEGARA", "WILAYAH")):
            if top is None or w[1] > top:     # lowest such word = the header cell, not the title
                top = w[1]
    if top is None:
        top = my0 - 60
    hdr = {i: [] for i in range(len(mids))}
    for w in words:
        if top - 6 <= w[1] and w[3] <= my0 + 1:
            xc = (w[0] + w[2]) / 2
            j = min(range(len(mids)), key=lambda k: abs(mids[k] - xc))
            hdr[j].append(w)
    headers = []
    for j in range(len(mids)):
        ws = sorted(hdr[j], key=lambda w: (round((w[1] + w[3]) / 20), w[0]))
        headers.append(" ".join(w[4] for w in ws).strip())
    # body: below marker row, stop at notes/source lines
    my1 = max(w[3] for w in marks)
    stop_y = 1e9
    for w in words:
        if w[1] > my1 and (w[4].startswith("Catatan") or w[4].startswith("Sumber") or w[4].startswith("Lanjutan")
                           or w[4].startswith("https://www.bps")):
            stop_y = min(stop_y, w[1])
    body = [w for w in words if w[1] > my1 - 0.5 and w[3] < stop_y + 0.5]
    # numeric words in data columns
    nums = [w for w in body if (w[0] + w[2]) / 2 > bound and looks_numeric(w[4])]
    labs = [w for w in body if (w[0] + w[2]) / 2 <= bound]
    stray = [w for w in body if (w[0] + w[2]) / 2 > bound and not looks_numeric(w[4])]
    # column centres: markers are reliable only if their count matches the clusters of numeric x-centres
    xs = sorted((w[0] + w[2]) / 2 for w in nums)
    clusters = []
    for x in xs:
        if clusters and x - clusters[-1][-1] <= 25:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    big = [c for c in clusters if len(c) > 2]
    if len(big) != len(clusters) and len(big) == len(mids) - 1:
        keep = {round(x, 3) for c in big for x in c}
        nums = [w for w in nums if round((w[0] + w[2]) / 2, 3) in keep]
        clusters = big
    ccent = [sum(c) / len(c) for c in clusters]
    col_source = "markers"
    if len(ccent) > len(mids) - 1:     # more numeric columns than markers (BPS marker typo) -> use clusters; fewer -> merged by tight spacing, keep markers
        col_source = "clusters(markers_mismatch:%d_markers_vs_%d_clusters)" % (len(mids) - 1, len(ccent))
        mids = [mids[0]] + ccent
        # label column header words only left of the boundary; rebuild headers for data columns
        hdr = {i: [] for i in range(len(mids))}
        for w in words:
            if top - 6 <= w[1] and w[3] <= my0 + 1:
                xc = (w[0] + w[2]) / 2
                j = min(range(len(mids)), key=lambda k: abs(mids[k] - xc))
                hdr[j].append(w)
        headers = []
        for j in range(len(mids)):
            ws = sorted(hdr[j], key=lambda w: (round((w[1] + w[3]) / 20), w[0]))
            headers.append(" ".join(w[4] for w in ws).strip())
    rows = []
    nl = _lines(nums, tol=2.5)
    ycs = [sum((w[1] + w[3]) / 2 for w in ln) / len(ln) for ln in nl]
    bands = []
    for i, yc in enumerate(ycs):
        lo = (ycs[i - 1] + yc) / 2 if i > 0 else -1e9
        hi = (ycs[i + 1] + yc) / 2 if i + 1 < len(ycs) else 1e9
        bands.append((lo, hi))
    lab_by_row = [[] for _ in nl]
    orphan = []
    for w in labs:
        yc = (w[1] + w[3]) / 2
        placed = False
        for i, (lo, hi) in enumerate(bands):
            if lo <= yc < hi and abs(yc - ycs[i]) <= 22:      # label lines are at most ~2 lines from the number row
                lab_by_row[i].append(w); placed = True; break
        if not placed:
            orphan.append(w)
    for i, ln in enumerate(nl):
        cells = [None] * len(mids)
        for w in ln:
            xc = (w[0] + w[2]) / 2
            j = min(range(len(mids)), key=lambda k: abs(mids[k] - xc))
            cells[j] = w[4] if cells[j] is None else cells[j] + " " + w[4]
        lw = sorted(lab_by_row[i], key=lambda w: (round((w[1] + w[3]) / 12), w[0]))
        label = " ".join(w[4] for w in lw).strip()
        rows.append(dict(label=label, cells=cells[1:], y=ycs[i]))
    year_words = []
    for w in words:
        if my0 - 48 <= w[1] and w[3] <= my0 + 1:
            mm = re.match(r"^((?:19|20)\d\d)\d?\D*$", w[4])
            if mm:
                year_words.append((int(mm.group(1)), (w[0] + w[2]) / 2))
    return dict(mids=mids, year_words=year_words, markers=colnum, col_source=col_source, headers=headers, rows=rows, stray=[w[4] for w in stray],
                orphan_labels=[w[4] for w in orphan])


def to_float(raw, decimal_hint=None):
    """Parse Indonesian/English formatted numbers. Returns (value|None, status, note).
    Footnote digits glued to the number (e.g. '1.068,692') are stripped when the pattern shows 3 decimals."""
    s = raw.strip() if raw else ""
    if not s:
        return None, "empty", ""
    if s in NA_TOKENS:
        return None, "NA" if s == "NA" else "dash", ""
    note = ""
    if re.fullmatch(r"-?\d{1,3}( \d{3})+(,\d+)?", s):      # thousands separated by a space (2019 edition)
        s = s.replace(" ", ""); note = "space_thousands"
    m = re.fullmatch(r"(-?\d+(?:\.\d{3})*),(\d+)", s)
    if m:
        dec = m.group(2)
        if len(dec) == 3:      # superscript footnote glued to a 2-decimal value
            dec = dec[:2]; note = "footnote_digit_stripped"
        return float(m.group(1).replace(".", "") + "." + dec), "ok", note
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        return float(s.replace(".", "")), "ok", "thousands_dot_integer"
    if re.fullmatch(r"-?\d+\.\d{1,2}", s) or re.fullmatch(r"-?\d+", s):
        return float(s), "ok", "dot_decimal" if "." in s else ""
    return None, "unparsed", ""
