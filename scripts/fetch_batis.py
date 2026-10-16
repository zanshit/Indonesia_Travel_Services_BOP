"""Fetch OECD-WTO BaTIS (OECD.SDD.TPS,DSD_BATIS@DF_BATIS,1.0) travel (SD/SDA/SDB) for Indonesia.
Run: python -I scripts/fetch_batis.py [--refresh]
Outputs: 02_raw/batis/*.csv + manifest.csv ; 03_extract/batis.csv, batis_reported_check.csv, anchor_checks_batis.csv"""
import importlib.util
import sys
from collections import Counter, defaultdict
from pathlib import Path

_spec = importlib.util.spec_from_file_location("sdmx_common", Path(__file__).resolve().parent / "sdmx_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

REFRESH = "--refresh" in sys.argv
RAW = C.RAW / "batis"
BASE = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BATIS@DF_BATIS,1.0/"
TAIL = ".S.SD+SDA+SDB.A.USD_EXC.N+F+B?startPeriod=2005&format=csvfilewithlabels"
URL_A = BASE + "IDN..X+M" + TAIL            # Indonesia as reporter
URL_B = BASE + ".IDN.X+M" + TAIL            # partners reporting Indonesia


def fetch_all(url_full, stem, key_builder):
    """Try full request; on failure split by TRADE_FLOW. Returns list of saved raw paths."""
    st, p = C.fetch(url_full, RAW, stem + ".csv", refresh=REFRESH)
    if st == 200:
        return [p]
    print(f"  full request failed (HTTP {st}); splitting by TRADE_FLOW", flush=True)
    paths = []
    for fl in ("X", "M"):
        st, p = C.fetch(key_builder(fl), RAW, f"{stem}_{fl}.csv", refresh=REFRESH)
        if st != 200:
            raise SystemExit(f"BaTIS fetch failed for flow {fl}: HTTP {st}")
        paths.append(p)
    return paths


paths_a = fetch_all(URL_A, "batis_idn_as_reporter", lambda fl: BASE + f"IDN..{fl}" + TAIL)
paths_b = fetch_all(URL_B, "batis_partners_reporting_idn", lambda fl: BASE + f".IDN.{fl}" + TAIL)
man = C.load_manifest(RAW)

FLIP = {"X": "debit", "M": "credit"}     # partner exports to IDN = Indonesians spending there
DIRECT = {"X": "credit", "M": "debit"}


def tidy(paths, line, flowmap):
    out = []
    for p in paths:
        m = man[p.name]
        for r in C.read_csv_rows(p):
            y, q = C.split_period(r["TIME_PERIOD"])
            out.append({
                "source": "OECD-WTO BaTIS", "line": line,
                "reporter": r["REF_AREA"], "partner_iso3": r["COUNTERPART_AREA"],
                "partner_name": r["Counterpart area"], "flow_idn": flowmap[r["TRADE_FLOW"]],
                "item": r["SERVICE"], "item_label": r["Service"], "year": y, "quarter": q,
                "value": r["OBS_VALUE"], "currency": r["CURRENCY"], "unit_mult": r["UNIT_MULT"],
                "adjustment": r["ADJUSTMENT"], "methodology_type": r["METHODOLOGY_TYPE"],
                "obs_status": r["OBS_STATUS"], "url": m["url"], "retrieved_at": m["retrieved_at_utc"],
                "_unit": r["UNIT_MEASURE"], "_reporter_name": r["Reference area"]})
    return out


rows_a = tidy(paths_a, "A_model", DIRECT)
rows_b = tidy(paths_b, "A_model_partnerside", FLIP)
for r in rows_a + rows_b:
    assert r["_unit"] == "USD_EXC", r
# uniqueness
keys = Counter((r["line"], r["reporter"], r["partner_iso3"], r["flow_idn"], r["item"], r["year"], r["adjustment"])
               for r in rows_a + rows_b)
dups = [k for k, v in keys.items() if v > 1]
print(f"rows A={len(rows_a)} B={len(rows_b)} duplicates={len(dups)}")
assert not dups
C.write_tidy(C.EXTRACT / "batis.csv", rows_a + rows_b)

# ---- batis_reported_check.csv (Indonesia as reporter only) ----
bykey = defaultdict(Counter)
for r in rows_a:
    k = (r["year"], r["item"])
    c = bykey[k]
    if r["adjustment"] == "N":
        c["n_reported_rows"] += 1
        if r["partner_iso3"] != "W":
            c["n_reported_rows_partner_not_world"] += 1
    if r["adjustment"] == "F":
        c["F_rows"] += 1
        c["F_" + (r["methodology_type"] or "blank")] += 1
meths = sorted({k for c in bykey.values() for k in c if k.startswith("F_") and k != "F_rows"})
import csv
with open(C.EXTRACT / "batis_reported_check.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["year", "item", "n_reported_rows", "n_reported_rows_partner_not_world", "F_rows"] + meths + ["source_url", "retrieved_at_utc"])
    for (y, it) in sorted(bykey):
        c = bykey[(y, it)]
        w.writerow([y, it, c["n_reported_rows"], c["n_reported_rows_partner_not_world"], c["F_rows"]] + [c[m] for m in meths] + [URL_A, man[paths_a[0].name]["retrieved_at_utc"]])

# ---- anchors ----
tr = rows_a
A = lambda partner, flow, adj, exp, name: dict(name=name, expected=exp, filt=dict(
    line="A_model", partner_iso3=partner, flow_idn=flow, item="SD", year="2023", adjustment=adj))
anchors = [
    A("AUS", "credit", "B", "3110.04", "BaTIS IDN->AUS 2023 SD adj B X (credit)"),
    A("AUS", "debit", "B", "1099.90", "BaTIS IDN->AUS 2023 SD adj B M (debit)"),
    A("W", "credit", "N", "14000.91", "BaTIS IDN->World 2023 SD adj N X (credit)"),
    A("W", "debit", "N", "11683.00", "BaTIS IDN->World 2023 SD adj N M (debit)"),
    A("SAU", "credit", "B", "158.78", "BaTIS IDN->SAU 2023 SD adj B X (credit)"),
    A("SAU", "debit", "B", "110.71", "BaTIS IDN->SAU 2023 SD adj B M (debit)"),
]
res = C.check_anchors(tr, anchors, C.EXTRACT / "anchor_checks_batis.csv")
print("DONE batis.csv rows:", len(rows_a) + len(rows_b), "anchors:", Counter(r["status"] for r in res))
