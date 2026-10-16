"""Extract the 'Indonesia' row from ABS ITSI CY2025 Tables 5,6,7,8 -> 03_extract/mirror_abs.csv (Indonesia perspective, flipped)."""
import csv, re, pathlib, openpyxl
ROOT = pathlib.Path(r"D:\Download\Indonesia_Travel_Services_BOP")
RAW = ROOT / "02_raw" / "abs"
OUT = ROOT / "03_extract" / "mirror_abs.csv"
BASE = "https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/2025/"
manifest = {r["file"]: r for r in csv.DictReader(open(RAW / "manifest.csv"))}
# (file, sheet-number prefix, ABS flow) ; ABS credit -> Indonesia debit, ABS debit -> Indonesia credit
FILES = [("536805500405.xlsx", 5, "credit"), ("536805500406.xlsx", 6, "debit"),
         ("536805500407.xlsx", 7, "credit"), ("536805500408.xlsx", 8, "debit")]
# BPM6 code maps by sub-table index k
BPM6_SERVICE = {1:"SA",2:"SB",3:"SC",4:"SD",5:"SE",6:"SF",7:"SG",8:"SH",9:"SI",10:"SJ",11:"SK",12:"SL",13:"S"}
BPM6_TRAVEL = {1:"SD",2:"SDA",3:"SDB",4:"SDB2",5:"ABS_OTHER_PERSONAL"}  # ABS 'Other' = personal travel excl. education (health + other personal), not a pure SDB3
COLS = ["source","line","reporter","partner_iso3","partner_name","flow_idn","item","item_label","year","quarter","value","currency","unit_mult","url","retrieved_at"]
FLIP = {"credit":"debit","debit":"credit"}
data = {}   # (item, label_key, year) -> {'credit':v,'debit':v}
meta = {}
rows_out = []
for f, n, absflow in FILES:
    wb = openpyxl.load_workbook(RAW / f, read_only=True, data_only=True)
    for sh in wb.sheetnames[1:]:
        k = int(sh.split(".")[1])
        allrows = list(wb[sh].iter_rows(values_only=True))
        title = str(allrows[3][0]).strip()
        title = re.sub(r"(\s*\([a-z]\))+\s*$", "", title)   # drop footnote markers
        hdr = next(r for r in allrows[:10] if any(isinstance(c, int) and 1990 < c < 2030 for c in r[1:3]))
        years = [(i, c) for i, c in enumerate(hdr) if isinstance(c, int)]
        ind = [r for r in allrows if r[0] and str(r[0]).strip() == "Indonesia"]
        assert len(ind) == 1, (f, sh)
        item = (BPM6_TRAVEL if n >= 7 else BPM6_SERVICE)[k]
        label = title
        for i, y in years:
            v = ind[0][i]
            if v is None or isinstance(v, str):
                v = 0 if (isinstance(v, str) and v.strip() == "-") else None
            if v is None: continue
            idn_flow = FLIP[absflow]
            val = abs(v)
            key = (5 if n in (5, 6) else 7, k, y)  # pairs 5<->6 and 7<->8
            data.setdefault(key, {})[idn_flow] = (val, item, label)
            rows_out.append({"source": f"ABS ITSI CY2025 Table {n}.{k}", "line": "B_mirror", "reporter": "AUS", "partner_iso3": "IDN",
                "partner_name": "Indonesia", "flow_idn": idn_flow, "item": item, "item_label": label, "year": y, "quarter": "",
                "value": val, "currency": "AUD", "unit_mult": 1000000, "url": BASE + f, "retrieved_at": manifest[f]["retrieved_at_utc"]})
# balance rows = Indonesia credit - Indonesia debit
for (grp, k, y), d in sorted(data.items()):
    if "credit" in d and "debit" in d:
        cv, item, clab = d["credit"]; dv, _, dlab = d["debit"]
        rows_out.append({"source": f"ABS ITSI CY2025 Tables {grp}.{k}+{grp+1}.{k}", "line": "B_mirror", "reporter": "AUS", "partner_iso3": "IDN",
            "partner_name": "Indonesia", "flow_idn": "balance", "item": item, "item_label": f"Balance (Indonesia credit - Indonesia debit): {re.sub(r'(Credits|Debits), ', '', re.sub(r'^Table [0-9.]+ ', '', clab))}",
            "year": y, "quarter": "", "value": cv - dv, "currency": "AUD", "unit_mult": 1000000,
            "url": BASE + [f for f, n, _ in FILES if n == grp][0] + " ; " + BASE + [f for f, n, _ in FILES if n == grp + 1][0],
            "retrieved_at": manifest[[f for f, n, _ in FILES if n == grp][0]]["retrieved_at_utc"]})
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows_out)
print(len(rows_out), "rows ->", OUT)
