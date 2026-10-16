"""Extract Travel + total Services (credit/debit/balance) from BI SEKI Table V.3 XLS -> 03_extract/bi_travel_totals.csv"""
import csv, pathlib, xlrd
ROOT = pathlib.Path(r"D:\Download\Indonesia_Travel_Services_BOP")
RAW = ROOT / "02_raw" / "bi"
OUT = ROOT / "03_extract" / "bi_travel_totals.csv"
URL = "https://www.bi.go.id/SEKI/tabel/TABEL5_3.xls"
man = {r["file"]: r for r in csv.DictReader(open(RAW / "manifest.csv"))}
RET = man["TABEL5_3.xls"]["retrieved_at_utc"]
wb = xlrd.open_workbook(RAW / "TABEL5_3.xls")
# sheet -> (header row of year, header row of Q, first year, label col)
SHEETS = {"Th 2004-2010": (10, 2004, 3), "5.3": (5, 2010, 2)}
BLOCKS = {"services_total": "Jasa-jasa", "travel": "D. Perjalanan"}
recs = {}   # (sheet,item,flow,year,quarter) -> (value, flag)
checks = []
def num(v):
    return v if isinstance(v, (int, float)) else None
for sh, (qrow, y0, lc) in SHEETS.items():
    ws = wb.sheet_by_name(sh)
    # quarter columns, grouped in blocks of Q1..Q4 ; year = y0 + block index
    qcols = [(c, str(ws.cell_value(qrow, c)).strip()) for c in range(ws.ncols) if str(ws.cell_value(qrow, c)).strip().startswith("Q")]
    blocks, cur = [], []
    for c, q in qcols:
        if q.startswith("Q1") and cur: blocks.append(cur); cur = []
        cur.append((c, q))
    blocks.append(cur)
    for item, label in BLOCKS.items():
        r0 = next(r for r in range(ws.nrows) if str(ws.cell_value(r, lc)).strip() == label)
        assert "Ekspor" in ws.cell_value(r0 + 1, lc) and "Impor" in ws.cell_value(r0 + 2, lc)
        for bi, blk in enumerate(blocks):
            year = y0 + bi
            q4 = blk[-1][0]
            # annual total column follows Q4; it sits at +1 or (in 2005, 2011 layouts) +2 columns
            ann_col = next((c for c in (q4 + 1, q4 + 2) if num(ws.cell_value(r0 + 1, c)) is not None), None)
            flags = []
            for c, q in blk:
                flag = "".join(ch for ch in q if ch == "*")
                flags.append(flag)
                qn = int(q[1])
                for flow, r in (("credit", r0 + 1), ("debit", r0 + 2), ("bi_net", r0)):
                    v = num(ws.cell_value(r, c))
                    if v is None: continue
                    recs[(sh, item, flow, year, qn)] = (abs(v) if flow == "debit" else v, flag)
            ann_flag = max(flags, key=len) if flags else ""   # annual header carries no marker in the file; derived as most provisional quarter flag
            for flow, r in (("credit", r0 + 1), ("debit", r0 + 2), ("bi_net", r0)):
                v = num(ws.cell_value(r, ann_col)) if ann_col else None
                if v is None: continue
                # only keep annual when all four quarters present
                if len(blk) == 4:
                    recs[(sh, item, flow, year, "")] = (abs(v) if flow == "debit" else v, ann_flag)
# Prefer sheet '5.3' for 2010 overlap; compare with old sheet
final = {}
for (sh, item, flow, y, q), val in recs.items():
    k = (item, flow, y, q)
    if k in final and sh == "Th 2004-2010":
        checks.append((k, final[k][0][0], val[0])); continue
    if k in final and sh == "5.3":
        checks.append((k, val[0], final[k][0][0]))
    final[k] = (val, sh)
rows = []
for (item, flow, y, q), ((v, flag), sh) in final.items():
    if flow == "bi_net": continue
    rows.append(dict(source=f"BI SEKI Table V.3 (sheet {sh})", item=item, flow_idn=flow, year=y, quarter=q, value=round(v, 2), currency="USD", unit="millions", status_flag=flag, url=URL, retrieved_at=RET))
for (item, flow, y, q), ((v, flag), sh) in sorted(final.items(), key=lambda kv: (kv[0][0], str(kv[0][2]), str(kv[0][3]))):
    pass
keys = {(i, y, q) for (i, f, y, q) in final}
for (i, y, q) in sorted(keys, key=lambda t: (t[0], t[1], str(t[2]))):
    c, d = final.get((i, "credit", y, q)), final.get((i, "debit", y, q))
    if c and d:
        net = final.get((i, "bi_net", y, q))
        bal = round(c[0][0] - d[0][0], 2)
        if net and abs(net[0][0] - bal) > 0.02: checks.append((("NETMISMATCH", i, y, q), bal, net[0][0]))
        rows.append(dict(source=f"BI SEKI Table V.3 (sheet {c[1]}); balance = credit - debit", item=i, flow_idn="balance", year=y, quarter=q, value=bal, currency="USD", unit="millions", status_flag=max(c[0][1], d[0][1], key=len), url=URL, retrieved_at=RET))
rows.sort(key=lambda r: (r["item"], r["year"], str(r["quarter"]), r["flow_idn"]))
cols = ["source","item","flow_idn","year","quarter","value","currency","unit","status_flag","url","retrieved_at"]
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", OUT)
bad = [c for c in checks if abs(c[1] - c[2]) > 0.02]
print("overlap/net checks:", len(checks), "diffs>0.02:", len(bad)); print(bad[:10])
# annual = sum of quarters check
for item in BLOCKS:
    for flow in ("credit", "debit"):
        for y in sorted({k[2] for k in final if k[0] == item and k[1] == flow}):
            qs = [final[(item, flow, y, q)][0][0] for q in (1,2,3,4) if (item, flow, y, q) in final]
            a = final.get((item, flow, y, ""))
            if a and len(qs) == 4 and abs(sum(qs) - a[0][0]) > 0.05: print("ANNUAL!=SUMQ", item, flow, y, sum(qs), a[0][0])
