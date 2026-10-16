"""Fetch OECD TIS (OECD.SDD.TPS,DSD_BOP@DF_TIS,1.0): partner-reported travel services with counterpart IDN.
Run: python -I scripts/fetch_oecd_tis.py [--refresh]
Outputs: 02_raw/oecd_tis/* + manifest.csv ; 03_extract/mirror_oecd_tis.csv, anchor_checks_oecd_tis.csv"""
import importlib.util
import sys
from collections import Counter
from pathlib import Path

_spec = importlib.util.spec_from_file_location("sdmx_common", Path(__file__).resolve().parent / "sdmx_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

REFRESH = "--refresh" in sys.argv
RAW = C.RAW / "oecd_tis"
BASE = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BOP@DF_TIS,1.0/"
MEAS = ["SD", "SDA", "SDB", "SDB1", "SDB2", "SDB3"]
Q = "?startPeriod=2005&format=csvfilewithlabels"
# key: REF_AREA.COUNTERPART_AREA.MEASURE.ACCOUNTING_ENTRY.FS_ENTRY.FREQ.UNIT_MEASURE.ADJUSTMENT
url_main = BASE + ".IDN." + "+".join(MEAS) + "...A+Q.." + Q
url_q = BASE + ".IDN." + "+".join(MEAS) + "...Q.." + Q
url_dsd = "https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.TPS/DSD_BOP@DF_TIS/1.0?references=all"

# structure (valid MEASURE codes) -- raw XML kept for the record
C.fetch(url_dsd, RAW, "dsd_DF_TIS_references_all.xml", is_csv=False, refresh=REFRESH)

paths = []
st, p = C.fetch(url_main, RAW, "tis_idn_annual_and_quarterly_request.csv", refresh=REFRESH)
if st == 200:
    paths.append(p)
else:
    print("multi-code request failed; fetching each MEASURE x FREQ separately", flush=True)
    for m in MEAS:
        for fq in ("A", "Q"):
            st, p = C.fetch(BASE + f".IDN.{m}...{fq}.." + Q, RAW, f"tis_idn_{m}_{fq}.csv", refresh=REFRESH)
            if st == 200:
                paths.append(p)
# explicit quarterly probe (records the outcome in the manifest even if empty/404)
stq, pq = C.fetch(url_q, RAW, "tis_idn_quarterly_probe.csv", refresh=REFRESH)
if stq == 200 and pq.name not in [x.name for x in paths]:
    # only add if the main request did not already include these rows
    paths.append(pq)
man = C.load_manifest(RAW)

OUT = {"C": "debit", "D": "credit", "B": "balance"}      # reporter entry -> Indonesia flow (flipped)
CUR = {"USD_EXC": "USD", "EUR_EXC": "EUR", "XDC": "XDC"}
rows, seen = [], set()
for pth in paths:
    m = man[pth.name]
    for r in C.read_csv_rows(pth):
        assert r["COUNTERPART_AREA"] == "IDN" and r["FS_ENTRY"] == "T", r
        y, q = C.split_period(r["TIME_PERIOD"])
        flow = OUT[r["ACCOUNTING_ENTRY"]]
        val = C.neg(r["OBS_VALUE"]) if flow == "balance" else r["OBS_VALUE"]
        key = (r["REF_AREA"], r["MEASURE"], r["ACCOUNTING_ENTRY"], r["UNIT_MEASURE"], r["TIME_PERIOD"], r["ADJUSTMENT"], r["FREQ"])
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "source": "OECD TIS", "line": "B_mirror", "reporter": r["REF_AREA"],
            "partner_iso3": "IDN", "partner_name": "Indonesia", "flow_idn": flow,
            "item": r["MEASURE"], "item_label": r["Measure"], "year": y, "quarter": q,
            "value": val, "currency": CUR[r["UNIT_MEASURE"]], "unit_mult": r["UNIT_MULT"],
            "adjustment": r["ADJUSTMENT"], "methodology_type": "", "obs_status": r["OBS_STATUS"],
            "url": m["url"], "retrieved_at": m["retrieved_at_utc"], "reporter_name": r["Reference area"]})
C.write_tidy(C.EXTRACT / "mirror_oecd_tis.csv", rows)

def A(rep, flow, exp, name):
    return dict(name=name, expected=exp, filt=dict(reporter=rep, flow_idn=flow, item="SD", year="2023", currency="USD"))
anchors = [
    A("AUS", "credit", "5852.4", "TIS AUS SD 2023 USD: reporter D 5852.4 -> IDN credit"),
    A("AUS", "debit", "1318.1", "TIS AUS SD 2023 USD: reporter C 1318.1 -> IDN debit"),
    A("AUS", "balance", "4534.3", "TIS AUS SD 2023 USD: reporter B -4534.3 -> IDN balance +4534.3"),
    A("JPN", "debit", "636.8", "TIS JPN SD 2023 USD: reporter C 636.8 -> IDN debit"),
    A("JPN", "credit", "419.0", "TIS JPN SD 2023 USD: reporter D 419.0 -> IDN credit"),
]
res = C.check_anchors(rows, anchors, C.EXTRACT / "anchor_checks_oecd_tis.csv")
# a reporter-side raw-orientation check: AUS reporter C/D/B raw values equal the user-given anchors
print("DONE mirror_oecd_tis.csv rows:", len(rows), "anchors:", Counter(r["status"] for r in res))
