"""Extract tables from downloaded BPS PDFs (text layer only) into tidy CSVs under 03_extract.

Run:  python -I scripts/extract_bps_pdfs.py [swn|pengeluaran|kunjungan|tsa|all]
Input : 02_raw/bps/pdf/*.pdf (unchanged raw files, produced by fetch_bps_pdfs.py)
Never estimates values from chart geometry: only printed text is used. Raster charts are handled
separately in the README (values not in a text layer are reported as such).
"""
import sys, os, re, csv, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymupdf
import pdf_tables as T
from bps_common import RAW_PDF, EXTRACT, write_csv

pymupdf.TOOLS.mupdf_display_errors(False)
SRC_NOTE = "BPS publication PDF via WebAPI download link (see 02_raw/bps/manifest.csv)"


def pdf_path(stem):
    m = glob.glob(os.path.join(RAW_PDF, stem + "__*.pdf"))
    return m[0] if m else None


def printed_page(page):
    lines = [l.strip() for l in page.get_text().split("\n") if l.strip()][:6]
    for l in lines:
        if re.fullmatch(r"\d{1,3}", l):
            return l
    return ""


def head_text(page, anchor_re=r"^(Lampiran|Tabel\s*:|Negara Tujuan Utama/|Negara/Wilayah/Entitas|Negara Tujuan Utama)\s*$"):
    lines = [l.strip() for l in page.get_text().split("\n") if l.strip()]
    out = []
    for l in lines:
        if re.match(anchor_re, l):
            break
        out.append(l)
    return " ".join(out)


# ----------------------------------------------------------------------------- SWN (outbound)
def classify(title_l):
    t = re.sub(r"\s+", " ", title_l).replace("/ ", "/")
    if "negara" not in t:
        return None
    if "sebelum dan setelah" in t:
        return "prepost_spend_by_destination"
    if "jumlah sampel" in t:
        return "sample_size_by_destination"
    if "lama perjalanan" in t and "pengeluaran" in t:
        return "spend_nights_pernight_by_destination"
    if "rata-rata lama perjalanan" in t:
        m = re.search(r"menurut negara[^()]*", t)
        return "nights_by_destination_year" if (m and " dan " not in m.group(0)) else None
    if t.startswith("rata-rata pengeluaran") or " rata-rata pengeluaran" in t[:40]:
        if re.search(r"dan maksud utama|dan tujuan utama perjalanan", t):
            return "spend_by_destination_purpose"
        if "jenis pengeluaran" in t:
            return "spend_by_destination_type"
        return None
    if "distribusi" in t:
        if re.search(r"dan maksud utama|dan tujuan utama perjalanan", t):
            return "share_by_destination_purpose"
        m = re.search(r"menurut negara[^()]*", t)
        if m and " dan " not in m.group(0):
            return "share_by_destination_year"
    return None


MEASURE = {
    "share_by_destination_year": ("trip_share_pct", "percent"),
    "share_by_destination_purpose": ("trip_share_pct_within_destination", "percent"),
    "spend_by_destination_purpose": ("spend_per_trip_usd", "USD"),
    "spend_by_destination_type": ("spend_per_trip_usd", "USD"),
    "prepost_spend_by_destination": ("prepost_spend_usd", "USD"),
    "sample_size_by_destination": ("n_samples", "count"),
    "nights_by_destination_year": ("avg_nights", "nights"),
}


def col_measure(family, header):
    h = header.lower()
    if family == "spend_nights_pernight_by_destination":
        if "lama" in h or "duration" in h:
            return "avg_nights", "nights"
        if re.search(r"per malam|per hari|per night|per day", h):
            return "spend_per_night_usd", "USD"
        return "spend_per_trip_usd", "USD"
    if family == "prepost_spend_by_destination":
        return ("pre_trip_spend_usd" if ("sebelum" in h or "pre" in h) else "post_trip_spend_usd"), "USD"
    return MEASURE[family]


def run_swn():
    rows, log = [], []
    for pf in sorted(glob.glob(os.path.join(RAW_PDF, "swn_*.pdf"))):
        stem = os.path.basename(pf).split("__")[0]
        ed = int(stem.split("_")[1])
        doc = pymupdf.open(pf)
        reg = {}            # table number -> (family, title)
        last = None
        for pi, page in enumerate(doc):
            txt = page.get_text()
            if "Table :" in txt or "Continued Table" in txt:       # English half of the 2022 edition
                continue
            res = T.read_table(page)
            if not res or not res["rows"]:
                continue
            ht = head_text(page)
            if not re.search(r"Negara|Entitas|Tujuan Utama", txt[:1500] + ht):
                continue
            mnum = re.search(r"(?:lanjutan (?:lampiran|tabel)|continued (?:appendix|table))\s*(\d+)", ht, re.I)
            if mnum:
                num = mnum.group(1)
                fam_title = reg.get(num)
                cont = True
            else:
                mt = re.search(r"(?<![\d.,])(\d{1,2})\s+((?:Distribusi|Rata-rata|Jumlah)[^$]*)", ht)
                if mt:
                    num, title = mt.group(1), mt.group(2)
                    title = re.split(r"\s+(?:Lampiran|Tabel)\b", title)[0]
                    fam_title = (classify(title.lower()), title)
                    reg[num] = fam_title
                    cont = False
                elif last:
                    num, fam_title = last; cont = True       # unlabeled continuation of previous page
                else:
                    continue
            last = (num, fam_title)
            if not fam_title or not fam_title[0]:
                log.append((ed, pi + 1, "Lampiran/Tabel " + str(num), "SKIPPED:" + (fam_title[1][:70] if fam_title else "no title"), len(res["rows"]), res["col_source"]))
                continue
            fam, title = fam_title
            # year(s)
            years = re.findall(r"(?:19|20)\d\d", title)
            is_range = bool(re.search(r"(?:19|20)\d\d\s*[–\-�]\s*(?:19|20)\d\d", title))
            single_year = None if is_range else (int(years[-1]) if years else ed)
            pg_pr = printed_page(page)
            tid = ("Tabel " if ed == 2022 else "Lampiran ") + num
            headers = res["headers"][1:]
            for r in res["rows"]:
                lab = r["label"]
                if not lab.strip():          # stray numerics in the page margin (e.g. year / page number): drop
                    continue
                pgnote = ""
                if pg_pr and lab.endswith(" " + pg_pr):       # printed page number glued onto the last label
                    lab = lab[: -len(pg_pr)].strip(); pgnote = "page_number_removed_from_label"
                clean = re.sub(r"(?<=[A-Za-z])\d$", "", lab).strip()
                for j, cell in enumerate(r["cells"]):
                    if cell is None:
                        continue
                    hdr = headers[j] if j < len(headers) else ""
                    val, status, note = T.to_float(cell)
                    if fam in ("share_by_destination_year", "nights_by_destination_year"):
                        ym = re.search(r"(?:19|20)\d\d", hdr)
                        yr = int(ym.group(0)) if ym else single_year
                        purpose = "ALL"
                    else:
                        yr = single_year or ed
                        purpose = ""
                    measure, unit = col_measure(fam, hdr)
                    if fam in ("share_by_destination_purpose", "spend_by_destination_purpose"):
                        purpose = re.sub(r"\s+", " ", hdr)
                    rows.append(dict(
                        edition=ed, year=yr, destination=clean, destination_label_raw=lab, purpose=purpose,
                        column_header=re.sub(r"\s+", " ", hdr), measure=measure, value=val, unit=unit,
                        trip_share_pct=val if measure == "trip_share_pct" else None,
                        spend_per_trip_usd=val if measure == "spend_per_trip_usd" else None,
                        value_raw=cell, value_status=status, note=(note + ";" + pgnote).strip(";"),
                        is_total=clean.lower().startswith("total"),
                        table_family=fam, source_page_pdf=pi + 1, source_page_printed=pg_pr,
                        figure_or_table_id=tid, table_title=re.sub(r"\s+", " ", title),
                        extraction_method="text layer, position-based (pdf_tables.read_table)",
                        column_source=res["col_source"], source_file=os.path.basename(pf)))
            log.append((ed, pi + 1, tid, fam, len(res["rows"]), res["col_source"]))
    # ---- values printed on RASTER charts of the 2025 edition (no text layer). Read from the rendered image labels;
    # nothing is estimated from bar geometry. Each value is cross-checked against the text-layer appendix table.
    FIG = "swn_2025__7344d8c9b1935d342f2ff9e7.pdf"
    fig_rows = []
    G2 = [("Malaysia", 29.25), ("Arab Saudi", 18.05), ("Singapura", 13.41), ("Tiongkok", 6.76), ("Thailand", 4.69),
          ("Jepang", 4.18), ("Timor Leste", 2.72), ("Kamboja", 2.43), ("Australia", 2.02), ("Korea Selatan", 2.00),
          ("ASEAN", 54.84), ("Timur Tengah", 20.27), ("Asia selain ASEAN", 16.94), ("Eropa", 4.00),
          ("Oseania", 2.30), ("Amerika", 1.39), ("Afrika", 0.26)]
    for d, v in G2:
        fig_rows.append((23, "5", "Gambar 2", "share_by_destination_year", d, "ALL", "trip_share_pct", "percent", v, "2025"))
    G9 = [("Malaysia", "Berlibur", 803.11), ("Malaysia", "Kesehatan/Kecantikan", 2844.83), ("Vietnam", "Berlibur", 885.40),
          ("Arab Saudi", "Keagamaan", 2604.82), ("Eropa", "Bisnis", 4162.58), ("Eropa", "Diklat/Kursus/Pendidikan", 6913.11)]
    for d, pu, v in G9:
        fig_rows.append((33, "15", "Gambar 9", "spend_by_destination_purpose", d, pu, "spend_per_trip_usd", "USD", v, "2025"))
    G17 = [("Malaysia", 63.95, 45.89), ("Singapura", 75.94, 53.04), ("Thailand", 91.17, 45.54), ("Vietnam", 46.96, 44.59),
           ("Jepang", 95.25, 52.76), ("Korea Selatan", 72.79, 37.26), ("Tiongkok", 107.80, 58.04),
           ("Arab Saudi", 186.94, 73.36), ("Australia", 74.16, 52.00)]
    for d, a, b in G17:
        fig_rows.append((49, "31", "Gambar 17", "prepost_spend_by_destination", d, "ALL", "pre_trip_spend_usd", "USD", a, "2025"))
        fig_rows.append((49, "31", "Gambar 17", "prepost_spend_by_destination", d, "ALL", "post_trip_spend_usd", "USD", b, "2025"))
    for pg, pp, tid, fam, d, pu, meas, unit, v, yr in fig_rows:
        # cross-check with appendix rows of the same edition
        hit = [r for r in rows if r["edition"] == 2025 and r["table_family"] == fam and r["measure"] == meas
               and r["year"] == int(yr)
               and (r["destination"].split("/")[0].strip().lower() == d.lower()
                    or r["destination"].split("/")[0].strip().lower().endswith(" " + d.lower()))
               and (fam != "spend_by_destination_purpose" or r["purpose"].lower().startswith(pu.lower()[:5]))
               and r["value"] is not None]
        if hit:
            chk = "matches appendix %s p%s" % (hit[0]["figure_or_table_id"], hit[0]["source_page_pdf"]) if abs(hit[0]["value"] - v) < 0.006 else "MISMATCH appendix value %s" % hit[0]["value"]
        else:
            chk = "not in appendix tables (figure-only value)"
        rows.append(dict(
            edition=2025, year=2025, destination=d, destination_label_raw=d, purpose=pu, column_header="",
            measure=meas, value=v, unit=unit,
            trip_share_pct=v if meas == "trip_share_pct" else None,
            spend_per_trip_usd=v if meas == "spend_per_trip_usd" else None,
            value_raw=str(v), value_status="ok", note="printed label on raster chart; " + chk, is_total=False,
            table_family="FIGURE:" + fam, source_page_pdf=pg, source_page_printed=pp, figure_or_table_id=tid,
            table_title="(figure in main text)", extraction_method="printed data label read visually from raster image (no text layer)",
            column_source="", source_file=FIG))
    for r in rows:   # encoding artefacts: U+FFFD stands for apostrophe or hyphen in labels/headers
        for k in ("destination", "destination_label_raw", "column_header", "purpose", "table_title"):
            if r[k]:
                r[k] = r[k].replace("�s", "'s").replace("�", "-")
    for r in rows:
        r["source_page"] = "pdf p%s / printed p%s" % (r["source_page_pdf"], r["source_page_printed"])
    hdr = ["edition", "year", "destination", "destination_label_raw", "purpose", "column_header", "measure", "value", "unit",
           "trip_share_pct", "spend_per_trip_usd", "value_raw", "value_status", "note", "is_total", "table_family",
           "source_page", "source_page_pdf", "source_page_printed", "figure_or_table_id", "table_title", "extraction_method",
           "column_source", "source_file"]
    write_csv(os.path.join(EXTRACT, "bps_outbound_by_destination.csv"), hdr, [[r[h] for h in hdr] for r in rows])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_swn_extract_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f)
    print("swn rows", len(rows), "tables parsed", len(log))
    for l in log: print(l)


# ----------------------------------------------------------------------------- Pengeluaran Wisman (inbound spend)
PENG_REGISTRY = {
    # edition: [(pdf_pages, family, table_id)]  -- pages verified against printed titles
    2025: [([129], "spend_per_visit_quarterly_by_nationality", "Lampiran 14"),
           ([130, 131], "spend_per_visit_by_type_by_nationality", "Lampiran 15"),
           ([143], "spend_nights_pernight_by_nationality", "Lampiran 27")],
    2024: [([106], "spend_per_visit_quarterly_by_nationality", "Lampiran 14"),
           ([107, 108], "spend_per_visit_by_type_by_nationality", "Lampiran 15"),
           ([120], "spend_nights_pernight_by_nationality", "Lampiran 27")],
    2023: [([92, 93, 94, 95], "spend_per_visit_by_type_by_nationality", "Lampiran 9"),
           ([105, 106], "spend_nights_pernight_by_nationality", "Lampiran 17")],
    2022: [([92, 93, 94], "spend_per_visit_by_type_by_nationality", "Tabel 13"),
           ([103], "spend_nights_pernight_by_nationality", "Tabel (number on preceding page)")],
    2021: [([64, 65, 66, 67, 68, 69], "spend_per_visit_by_type_by_nationality", "Tabel 16"),
           ([79, 80], "spend_per_night_by_nationality_2021", "Tabel 22")],
    2019: [([50, 51], "spend_per_visit_timeseries_by_residence", "Tabel 6"),
           ([52, 53], "spend_per_visit_by_type_by_nationality", "Tabel 7")],
}


def run_pengeluaran():
    rows, log = [], []
    for pf in sorted(glob.glob(os.path.join(RAW_PDF, "pengeluaran_wisman_*.pdf"))):
        stem = os.path.basename(pf).split("__")[0]
        ed = int(stem.split("_")[2])
        doc = pymupdf.open(pf)
        for pages, fam, num in PENG_REGISTRY.get(ed, []):
          for pn in pages:
            pi = pn - 1
            page = doc[pi]
            res = T.read_table(page)
            if not res or not res["rows"]:
                log.append((ed, pn, num, fam, 0, "NO TABLE FOUND"))
                continue
            title = re.sub(r"\s+", " ", head_text(page, anchor_re=r"^(Lampiran|Appendix|Tabel\s*:|Kebangsaan|KEBANGSAAN|NEGARA TEMPAT TINGGAL|Negara Tempat Tinggal)\s*$"))[:160]
            years = re.findall(r"(?:19|20)\d\d", title)
            single_year = int(years[-1]) if years else ed
            pg_pr = printed_page(page)
            headers = res["headers"][1:]
            for r in res["rows"]:
                lab = r["label"].strip()
                if not lab:
                    continue
                if pg_pr and lab.endswith(" " + pg_pr):
                    lab = lab[: -len(pg_pr)].strip()
                clean = re.sub(r"(?<=[A-Za-z])\d$", "", lab).strip()
                low = clean.lower()
                kind = ("total" if re.match(r"(jumlah|total|rata-?\s*rata)", low) else
                        "group" if re.match(r"\d+\.\s", clean) else "row")
                for j, cell in enumerate(r["cells"]):
                    if cell is None:
                        continue
                    hdr = re.sub(r"\s+", " ", headers[j]) if j < len(headers) else ""
                    val, status, note = T.to_float(cell)
                    hl = hdr.lower()
                    year = single_year
                    period = ""
                    if fam == "spend_per_visit_quarterly_by_nationality":
                        mq = re.search(r"triwulan\s+(iv|iii|ii|i)\b", hl)
                        period = ("Q" + {"i": "1", "ii": "2", "iii": "3", "iv": "4"}[mq.group(1)]) if mq else "annual"
                        measure, unit = "spend_per_visit_usd", "USD"
                    elif fam == "spend_per_visit_timeseries_by_residence":
                        ym = re.match(r"^(20\d\d|19\d\d)", hdr.strip())
                        year = int(ym.group(1)) if ym else None
                        period = "annual"
                        measure, unit = "spend_per_visit_usd", "USD"
                    elif fam == "spend_nights_pernight_by_nationality":
                        if "lama" in hl or "duration" in hl:
                            measure, unit = "avg_length_of_stay_nights", "nights"
                        elif re.search(r"per malam|per night|per hari|per day", hl):
                            measure, unit = "spend_per_night_usd", "USD"
                        else:
                            measure, unit = "spend_per_visit_usd", "USD"
                        period = "annual"
                    elif fam == "spend_per_night_by_nationality_2021":
                        measure, unit = "spend_per_night_usd", "USD"
                        period = hdr
                    else:
                        measure, unit = "spend_per_visit_usd", "USD"
                        period = hdr
                    rows.append(dict(edition=ed, year=year, nationality_label_raw=lab, nationality=clean, row_kind=kind,
                                     table_family=fam, column_header=hdr, period_or_component=period, measure=measure,
                                     unit=unit, value=val, value_raw=cell.strip(), value_status=status, note=note,
                                     source_page_pdf=pi + 1, source_page_printed=pg_pr,
                                     table_id=num,
                                     table_title=title[:160], column_source=res["col_source"],
                                     extraction_method="text layer, position-based (pdf_tables.read_table)",
                                     source_file=os.path.basename(pf)))
            log.append((ed, pi + 1, num, fam, len(res["rows"]), res["col_source"]))
    for r in rows:
        for k in ("nationality", "nationality_label_raw", "column_header", "table_title"):
            if r[k]:
                r[k] = r[k].replace("\ufffd", "-")
    hdr = ["edition", "year", "nationality_label_raw", "nationality", "row_kind", "table_family", "column_header",
           "period_or_component", "measure", "unit", "value", "value_raw", "value_status", "note", "source_page_pdf",
           "source_page_printed", "table_id", "table_title", "column_source", "extraction_method", "source_file"]
    write_csv(os.path.join(EXTRACT, "bps_spend_per_visit_detail.csv"), hdr, [[r[h] for h in hdr] for r in rows])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pengeluaran_extract_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f)
    print("pengeluaran rows", len(rows), "tables", len(log))
    for l in log:
        print(l)


# ----------------------------------------------------------------------------- Kunjungan Wisman (arrivals by nationality)
KUNJ_REGISTRY = {
    # edition: (pdf pages, table id)  -- annual arrivals by nationality, multi-year table (+ continuation pages)
    2016: ([31, 32], "Tabel 4 (2003-2016)"), 2017: ([31, 32], "Tabel 4 (2004-2017)"),
    2018: ([35, 36], "Tabel 4 (2005-2018)"), 2019: ([32, 33], "Tabel 4 (2006-2019)"),
    2020: ([40, 41], "Tabel 4 (2007-2020)"), 2021: ([35, 36], "Tabel 4 (2008-2021)"),
    2022: ([60], "Tabel 4 (title 2009-2022; page shows 2018-2022)"), 2023: ([61], "Lampiran 4 (2019-2023)"),
    2024: ([70], "Lampiran 3 (2020-2024)"), 2025: ([74], "Lampiran 3 (2021-2025)"),
}


def run_kunjungan():
    rows, log = [], []
    for pf in sorted(glob.glob(os.path.join(RAW_PDF, "kunjungan_wisman_*.pdf"))):
        stem = os.path.basename(pf).split("__")[0]
        ed = int(stem.split("_")[2])
        if ed not in KUNJ_REGISTRY:
            continue
        pages, tid = KUNJ_REGISTRY[ed]
        doc = pymupdf.open(pf)
        for pn in pages:
            page = doc[pn - 1]
            res = T.read_table(page)
            if not res or not res["rows"]:
                log.append((ed, pn, tid, 0, "NO TABLE")); continue
            pg_pr = printed_page(page)
            mids = res["mids"][1:]
            colyear = []
            for m in mids:
                cand = [(abs(x - m), y) for y, x in res["year_words"] if abs(x - m) < 40]
                colyear.append(min(cand)[1] if cand else None)
            n = 0
            for r in res["rows"]:
                lab = re.sub(r"\s+", " ", r["label"]).strip()
                if not lab or lab.startswith(("*", ")")) or re.search(r"Statistik Kunjungan|International Visitor|^\d+ Statistik", lab):
                    continue
                if pg_pr and lab.endswith(" " + pg_pr):
                    lab = lab[: -len(pg_pr)].strip()
                clean = re.sub(r"(?<=[A-Za-z])\d$", "", lab).strip()
                up = clean.upper()
                kind = "grand_total" if up.startswith(("GRAND TOTAL", "JUMLAH")) else "subtotal" if up.startswith("TOTAL") else "row"
                for j, cell in enumerate(r["cells"]):
                    if cell is None or j >= len(colyear) or colyear[j] is None:
                        continue
                    val, status, note = T.to_float(cell)
                    rows.append(dict(edition=ed, year=colyear[j], nationality_label_raw=lab, nationality=clean, row_kind=kind,
                                     arrivals=None if val is None else int(val), value_raw=cell.strip(), value_status=status,
                                     note=note, source_page_pdf=pn, source_page_printed=pg_pr, table_id=tid,
                                     column_source=res["col_source"],
                                     extraction_method="text layer, position-based (pdf_tables.read_table); year from header words nearest each column",
                                     source_file=os.path.basename(pf)))
                    n += 1
            log.append((ed, pn, tid, len(res["rows"]), res["col_source"], sorted({y for y in colyear if y})))
    for r in rows:
        for k in ("nationality", "nationality_label_raw"):
            if r[k]:
                r[k] = r[k].replace("\ufffd", "-")
    hdr = ["edition", "year", "nationality_label_raw", "nationality", "row_kind", "arrivals", "value_raw", "value_status", "note",
           "source_page_pdf", "source_page_printed", "table_id", "column_source", "extraction_method", "source_file"]
    write_csv(os.path.join(EXTRACT, "bps_arrivals_by_nationality_pub.csv"), hdr, [[r[h] for h in hdr] for r in rows])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_kunjungan_extract_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f)
    print("kunjungan rows", len(rows), "tables", len(log))
    for l in log:
        print(l)


# ----------------------------------------------------------------------------- TSA 2023-2025 (table list only)
TSA_TABLES = [
    # (appendix no, title (BPS wording), pdf page, printed page, rows are..., country breakdown)
    ("Lampiran 1", "Pengeluaran Wisatawan Inbound ke Indonesia menurut Produk (miliar rupiah), 2023-2025", 98, 80, "tourism products (services)", "no"),
    ("Lampiran 2", "Pengeluaran Wisatawan Nusantara (Domestik) menurut Produk (miliar rupiah), 2023-2025", 99, 81, "tourism products", "no"),
    ("Lampiran 3", "Pengeluaran Wisatawan Outbound Indonesia menurut Produk (miliar rupiah), 2023-2025", 100, 82, "tourism products", "no"),
    ("Lampiran 4", "Konsumsi Pariwisata Internal Indonesia menurut Produk (miliar rupiah), 2023-2025", 101, 83, "tourism products", "no"),
    ("Lampiran 5", "Nilai Tambah Bruto Industri Pariwisata Indonesia menurut Industri (miliar rupiah), 2023-2025", 102, 84, "industries", "no"),
    ("Lampiran 6.1", "Supply Domestik (miliar rupiah), 2023-2025", 103, 85, "tourism products", "no"),
    ("Lampiran 6.2", "Rasio Produk Pariwisata, 2023-2025", 104, 86, "tourism products", "no"),
    ("Lampiran 6.3-6.5", "Indikator Ekonomi Pariwisata Indonesia; Indikator Ekonomi Indonesia; Kontribusi Pariwisata Indonesia, 2023-2025", 105, 87, "indicators", "no"),
    ("Lampiran 6.6", "Tourism Direct GDP (TDGDP) dan PDB ADHB (miliar rupiah), 2023-2025", 106, 88, "indicators", "no"),
    ("Lampiran 6.7", "Pengeluaran Pariwisata Inbound dan Ekspor ADHB (miliar rupiah), 2023-2025", 107, 89, "years (inbound spending vs total exports, totals only)", "no"),
    ("Lampiran 6.8", "Pengeluaran Pariwisata Nusantara dan PKRT ADHB (miliar rupiah), 2023-2025", 108, 90, "years", "no"),
    ("Lampiran 6.9", "Konsumsi Pariwisata Internal, PKRT dan Ekspor ADHB (miliar rupiah), 2023-2025", 109, 91, "years", "no"),
    ("Lampiran 7", "Jumlah Tenaga Kerja Pariwisata menurut Industri Pariwisata, 2023-2025", 110, 92, "industries", "no"),
    ("Lampiran 8", "Konsumsi Kolektif Pariwisata menurut Produk (juta rupiah), 2023-2025", 111, 93, "tourism products", "no"),
    ("Lampiran 9", "Klasifikasi Produk dan Industri Pariwisata Indonesia", 112, 94, "classification", "n/a"),
    ("Lampiran 10", "Konkordansi Klasifikasi Industri Pariwisata ke KBLI dan PDB", 113, 95, "classification", "n/a"),
    ("Lampiran 11", "Konkordansi Klasifikasi Produk Pariwisata ke KBKI 2010 dan PDB", 119, 101, "classification", "n/a"),
]


def run_tsa():
    pf = glob.glob(os.path.join(RAW_PDF, "tsa_2023_2025__*.pdf"))[0]
    doc = pymupdf.open(pf)
    rows = []
    for no, title, pdfp, prp, rowsare, cb in TSA_TABLES:
        t = re.sub(r"\s+", " ", doc[pdfp - 1].get_text())
        ok = "printed page %d found on PDF page" % prp if re.search(r"(^|\s)%d(\s|$)" % prp, t[:200]) else "printed page not confirmed"
        rows.append([no, title, pdfp, prp, rowsare, cb, ok,
                     "Appendix table list in TOC pp.15-16; pages verified by reading the page text"])
    rows.append(["(text figure)", "Gambar 2.6 Persentase 10 Negara Tujuan Utama Wisatawan Nasional (persen), 2025 -- share of OUTBOUND TRIPS by destination, "
                 "copied from Statistik Wisatawan Nasional 2025; text-layer labels", 36, 18,
                 "10 destination countries (percent of trips, not expenditure)", "partial: trips only, no spending",
                 "values: Malaysia 29.25, Arab Saudi 18.05, Singapura 13.41, Tiongkok 6.76, Tailan 4.69, Jepang 4.18, Timor Leste 2.72, Kamboja 2.43, Australia 2.02, Korea Selatan 2.00",
                 "only country-level item found in the TSA PDF (keyword search for country names: pdf pages 36-37 only)"])
    write_csv(os.path.join(EXTRACT, "bps_tsa_table_list.csv"),
              ["appendix_no", "title", "pdf_page", "printed_page", "rows_are", "inbound_outbound_expenditure_by_country", "page_check_or_values", "note"], rows)
    print("tsa rows", len(rows))


# ----------------------------------------------------------------------------- length of stay in the arrivals publications
LOS_REGISTRY = [  # (edition, pdf page, table id, basis)
    (2025, 100, "Lampiran 11", "Imigrasi + Mobile Positioning Data (matches var 356)"),
    (2025, 101, "Lampiran 12", "Imigrasi only"),
    (2024, 96, "Lampiran 11", "Imigrasi + Mobile Positioning Data (matches var 356)"),
    (2024, 97, "Lampiran 12", "Imigrasi only"),
]


def run_los():
    rows = []
    for ed, pn, tid, basis in LOS_REGISTRY:
        pf = glob.glob(os.path.join(RAW_PDF, "kunjungan_wisman_%d__*.pdf" % ed))[0]
        page = pymupdf.open(pf)[pn - 1]
        res = T.read_table(page)
        if not res:
            continue
        pg_pr = printed_page(page)
        mids = res["mids"][1:]
        colyear = []
        for m in mids:
            cand = [(abs(x - m), y) for y, x in res["year_words"] if abs(x - m) < 40]
            colyear.append(min(cand)[1] if cand else None)
        for r in res["rows"]:
            lab = re.sub(r"\s+", " ", r["label"]).strip()
            if not lab or re.search(r"Statistik Kunjungan|International Visitor", lab):
                continue
            if pg_pr and lab.endswith(" " + pg_pr):
                lab = lab[: -len(pg_pr)].strip()
            for j, cell in enumerate(r["cells"]):
                if cell is None or j >= len(colyear) or colyear[j] is None:
                    continue
                val, status, note = T.to_float(cell)
                rows.append([ed, colyear[j], lab.replace("\ufffd", "-"), val, cell.strip(), status, pn, pg_pr, tid, basis,
                             os.path.basename(pf)])
    write_csv(os.path.join(EXTRACT, "bps_length_of_stay_pub.csv"),
              ["edition", "year", "nationality_label_raw", "avg_length_of_stay_nights", "value_raw", "value_status",
               "source_page_pdf", "source_page_printed", "table_id", "basis", "source_file"], rows)
    print("los rows", len(rows))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("swn", "all"):
        run_swn()
    if which in ("pengeluaran", "all"):
        run_pengeluaran()
    if which in ("kunjungan", "all"):
        run_kunjungan()
    if which in ("tsa", "all"):
        run_tsa()
    if which in ("los", "all"):
        run_los()
