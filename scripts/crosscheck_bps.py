"""Cross-checks between BPS WebAPI variables and BPS publication tables. Writes 03_extract/bps_crosscheck.csv
and prints a summary. No credit/debit products are computed here; only like-for-like comparisons.

Run:  python -I scripts/crosscheck_bps.py
"""
import os, sys, csv, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bps_common import EXTRACT, write_csv
from build_bps_nationality_rows import classify

def rd(name):
    return list(csv.DictReader(open(os.path.join(EXTRACT, name), encoding="utf-8-sig")))

def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

out = []   # check, key, year, a_label, a, b_label, b, diff, status

def add(check, key, year, al, a, bl, b):
    if a is None or b is None:
        return
    d = a - b
    out.append([check, key, year, al, a, bl, b, round(d, 4), "match" if abs(d) < 0.006 else "DIFF"])

# ---- A. var 272 / var 356 versus publications
v272 = collections.defaultdict(dict)
for r in rd("bps_spend_per_visit_by_nationality.csv"):
    k = classify(r["row_label_clean"])[0]
    v272[(k, int(r["year"]))] = f(r["value"])
v356 = {}
for r in rd("bps_length_of_stay_by_nationality.csv"):
    v356[(classify(r["row_label_clean"])[0], int(r["year"]))] = f(r["value"])

pub = rd("bps_spend_per_visit_detail.csv")
# publication: annual spend per visit by nationality (edition year == data year), from the quarterly table or the L-table
P_spend, P_los, P_ts = {}, {}, {}
for r in pub:
    k = classify(r["nationality"])[0]
    y = int(r["year"]) if r["year"] else None
    if r["table_family"] == "spend_per_visit_quarterly_by_nationality" and r["period_or_component"] == "annual":
        P_spend[("quarterly_tbl", k, y)] = f(r["value"])
    elif r["table_family"] == "spend_nights_pernight_by_nationality":
        if r["measure"] == "spend_per_visit_usd":
            P_spend[("L_tbl_ed%s" % r["edition"], k, y)] = f(r["value"])
        elif r["measure"] == "avg_length_of_stay_nights":
            P_los[(r["edition"], k, y)] = f(r["value"])
    elif r["table_family"] == "spend_per_visit_timeseries_by_residence":
        P_ts[(k, y)] = f(r["value"])
for (src, k, y), val in P_spend.items():
    if (k, y) in v272:
        add("A1 var272 vs publication spend/visit [%s]" % src, k, y, "var272", v272[(k, y)], src, val)
for (k, y), val in P_ts.items():
    if (k, y) in v272:
        add("A2 var272 vs 2019-edition series 2009-2019 (Tabel 6)", k, y, "var272", v272[(k, y)], "pub2019", val)
for (ed, k, y), val in P_los.items():
    if (k, y) in v356:
        add("A3 var356 vs publication length of stay [ed%s]" % ed, k, y, "var356", v356[(k, y)], "pub", val)

# var 356 vs the arrivals publication (immigration + MPD basis)
for r in rd("bps_length_of_stay_pub.csv"):
    if r["table_id"] == "Lampiran 11":
        k = classify(r["nationality_label_raw"])[0]
        y = int(r["year"])
        if (k, y) in v356:
            add("A4 var356 vs Kunjungan publication Lampiran 11 (Imigrasi+MPD) [ed%s]" % r["edition"], k, y, "var356", v356[(k, y)], "pub", f(r["avg_length_of_stay_nights"]))

# ---- B. var 1470 annual sums vs publication arrivals tables
ann = {}
for r in rd("bps_arrivals_by_nationality_annual.csv"):
    ann[(classify(r["row_label_clean"])[0], int(r["year"]))] = (f(r["sum_of_months_1_12"]), r["year_completeness_flag"])
pubarr = rd("bps_arrivals_by_nationality_pub.csv")
for r in pubarr:
    k = classify(r["nationality"])[0]
    y = int(r["year"])
    if (k, y) in ann and ann[(k, y)][1] == "complete":
        add("B1 var1470 annual sum vs publication arrivals [ed%s]" % r["edition"], k, y, "var1470", ann[(k, y)][0], "pub", f(r["arrivals"]))

# ---- C. SWN: same destination/year in different editions (revisions) ; var 2195 total vs text total
swn = rd("bps_outbound_by_destination.csv")
share = collections.defaultdict(dict)
for r in swn:
    if r["table_family"] == "share_by_destination_year" and r["value"]:
        k = r["destination"].split("/")[0].strip().lower()
        share[(k, int(r["year"]))][int(r["edition"])] = float(r["value"])
for (k, y), eds in share.items():
    base = max(eds)
    for e2, v in eds.items():
        if e2 != base:
            add("C1 SWN trip share: edition %d vs latest edition %d" % (e2, base), k, y, "ed%d" % e2, v, "ed%d" % base, eds[base])
tot = {}
for r in swn:
    if r["table_family"] == "spend_nights_pernight_by_destination" and r["is_total"] == "True" and r["measure"] == "spend_per_trip_usd":
        tot[int(r["edition"])] = float(r["value"])
trips = {}
for r in rd("bps_outbound_trips.csv"):
    if r["row_label_clean"] == "Jumlah" and r["period_label"] == "Tahunan":
        trips[int(r["year"])] = float(r["value"])
add("C2 SWN 2025 text total trips (9,165,894) vs var 2195 Jumlah/Tahunan 2025", "TOTAL", 2025, "SWN text p.10", 9165894.0, "var2195", trips.get(2025))
add("C3 SWN 2025 avg spend/trip (text exec summary 1,875.27) vs Lampiran 28 total", "TOTAL", 2025, "text", 1875.27, "Lampiran 28", tot.get(2025))

# ---- D. anchor: var 272 2024 Rata-Rata
add("D1 anchor: var272 2024 'Rata- Rata' vs news 1,391.85", "TOTAL:AVERAGE_OR_TOTAL", 2024, "var272", v272.get(("TOTAL:AVERAGE_OR_TOTAL", 2024)), "news", 1391.85)
for k, lab in (("MYS", "Malaysia"), ("SGP", "Singapura"), ("THA", "Thailand"), ("BRN", "Brunei"), ("PHL", "Filipina")):
    out.append(["D2 anchor range 700-1,400 USD (task note) for 2024", k, 2024, "var272", v272.get((k, 2024)), "range", "700-1400",
                "", "in_range" if v272.get((k, 2024)) and 700 <= v272[(k, 2024)] <= 1400 else "OUT_OF_RANGE (%s)" % lab])

write_csv(os.path.join(EXTRACT, "bps_crosscheck.csv"),
          ["check", "key", "year", "a_label", "a_value", "b_label", "b_value", "a_minus_b", "status"], out)

summ = collections.defaultdict(lambda: collections.Counter())
for r in out:
    summ[r[0]][r[8]] += 1
for c, cnt in sorted(summ.items()):
    print(c, dict(cnt))
print("rows", len(out))
