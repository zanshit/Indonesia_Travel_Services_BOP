"""Fetch BPS WebAPI variables, publication lists and publication details; write tidy CSVs.

Run:  python -I scripts\fetch_bps_api.py [--refresh]
Reads BPS_API_KEY from the environment. Raw JSON -> 02_raw\bps\api (cached; --refresh re-downloads).
Only the WebAPI host is used (never www.bps.go.id).
"""
import sys, os, json, re, html, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bps_common as C
from bps_common import HOST, api_json, write_csv, EXTRACT

CACHE = "--refresh" not in sys.argv
SRC = "BPS WebAPI https://webapi.bps.go.id/v1/api/list/model/data (domain 0000, var {v})"
VARS = [272, 356, 1470, 331, 1160, 2195]


def clean_label(s):
    """Unescape HTML, strip tags, collapse letter-spaced words ('R u s i a' -> 'Rusia')."""
    s = html.unescape(re.sub(r"<[^>]+>", "", html.unescape(s))).strip()
    if re.fullmatch(r"(?:\S ){2,}\S", s):
        s = s.replace(" ", "")
    return re.sub(r"\s+", " ", s)


def row_kind(clean):
    c = clean.lower()
    if re.fullmatch(r"rata-?\s*rata|jumlah|grand total", c):
        return "grand_total_or_average"
    if c.startswith("total ") or c == "asean":
        return "region_subtotal"
    if re.match(r"(other |lain|negara lainnya|asean lainnya)", c) or c in ("central america", "south america", "amerika tengah", "amerika selatan"):
        return "residual_or_regional_group"
    return "country_or_entity"



def paged(path_tail, base):
    """Fetch all pages of a list endpoint; returns list of items. Raw saved per page."""
    items, p = [], 1
    while True:
        d = api_json(f"{path_tail}page/{p}/", f"{base}_p{p}.json", cache=CACHE)
        if d.get("data-availability") != "available":
            return items, d.get("data-availability")
        meta, rows = d["data"][0], d["data"][1]
        items += rows
        if p >= meta["pages"]:
            return items, "available"
        p += 1


def fetch_var(v):
    th, _ = paged(f"list/model/th/domain/0000/var/{v}/", f"var{v}_th")
    vv, _ = paged(f"list/model/vervar/domain/0000/var/{v}/", f"var{v}_vervar")
    out = []  # list of dict rows
    meta = {"var_id": v, "years_available": [(t["th_id"], t["th"]) for t in th], "vervar_n": len(vv)}
    for t in th:
        d = api_json(f"list/model/data/lang/ind/domain/0000/var/{v}/th/{t['th_id']}/",
                     f"var{v}_data_th{t['th_id']}.json", cache=CACHE)
        if d.get("data-availability") != "available":
            meta.setdefault("unavailable_years", []).append(t["th"])
            continue
        var = d["var"][0]
        meta["label"] = var["label"].strip(); meta["unit"] = var["unit"]
        meta["last_update"] = d.get("last_update")
        # decode keys: vervar_id + var_id + turvar_id + th_id + turth_id (verified by unique reverse map)
        lut = {}
        for a in d["vervar"]:
            for b in d["turvar"]:
                for c in d["tahun"]:
                    for e in d["turtahun"]:
                        k = f"{a['val']}{v}{b['val']}{c['val']}{e['val']}"
                        assert k not in lut, f"ambiguous key {k} var {v} th {t['th_id']}"
                        lut[k] = (a, b, c, e)
        for k, val in d["datacontent"].items():
            if k not in lut:
                raise RuntimeError(f"undecodable key {k} var {v} th {t['th_id']}")
            a, b, c, e = lut[k]
            out.append(dict(var_id=v, var_label=var["label"].strip(), unit=var["unit"],
                            year=int(c["label"]), period_id=e["val"], period_label=e["label"],
                            row_id=a["val"], row_label=a["label"].strip(), row_label_clean=clean_label(a["label"]),
                            row_kind=row_kind(clean_label(a["label"])), value=val,
                            is_total_row=row_kind(clean_label(a["label"])) in ("grand_total_or_average", "region_subtotal"),
                            last_update=d.get("last_update"), source=SRC.format(v=v)))
    out.sort(key=lambda r: (r["year"], r["period_id"], r["row_id"]))
    meta["rows_with_values"] = len(out)
    return out, vv, meta


HDR = ["var_id", "var_label", "unit", "year", "period_id", "period_label", "row_id", "row_label", "row_label_clean",
       "row_kind", "is_total_row", "value", "last_update", "source"]


def to_rows(recs):
    return [[r[h] for h in HDR] for r in recs]


def main():
    os.makedirs(EXTRACT, exist_ok=True)
    data, vervars, metas = {}, {}, {}
    for v in VARS:
        print(f"[var {v}] fetching ...", flush=True)
        data[v], vervars[v], metas[v] = fetch_var(v)
        print(f"   years={[y for _, y in metas[v]['years_available']]} rows={len(data[v])}", flush=True)

    # ---- 272, 356: one row per nationality x year (period 0 = Tahun)
    write_csv(f"{EXTRACT}\\bps_spend_per_visit_by_nationality.csv", HDR, to_rows(data[272]))
    write_csv(f"{EXTRACT}\\bps_length_of_stay_by_nationality.csv", HDR, to_rows(data[356]))

    # ---- 1470 monthly + annual
    m = [r for r in data[1470] if 1 <= r["period_id"] <= 12]
    write_csv(f"{EXTRACT}\\bps_arrivals_by_nationality_monthly.csv", HDR, to_rows(m))
    rep = {(r["year"], r["row_id"]): r["value"] for r in data[1470] if r["period_id"] == 13}
    label = {r["row_id"]: r["row_label"] for r in data[1470]}
    istot = {r["row_id"]: r["is_total_row"] for r in data[1470]}
    lclean = {r["row_id"]: r["row_label_clean"] for r in data[1470]}
    lkind = {r["row_id"]: r["row_kind"] for r in data[1470]}
    agg = {}
    for r in m:
        a = agg.setdefault((r["year"], r["row_id"]), {})
        a[r["period_id"]] = r["value"]
    years = sorted({y for y, _ in agg} | {y for y, _ in rep})
    # months present in the GRAND TOTAL row decide the year-level flag
    gt = [rid for rid, l in lclean.items() if l.upper() == "GRAND TOTAL"]
    ann = []
    yearflag = {}
    for y in years:
        mon = set(agg.get((y, gt[0]), {})) if gt else set()
        miss = [x for x in range(1, 13) if x not in mon]
        yearflag[y] = ("complete" if not miss else f"INCOMPLETE: grand-total months missing {miss}")
    for (y, rid) in sorted(set(agg) | set(rep), key=lambda k: (k[0], k[1])):
        a = agg.get((y, rid), {})
        s = sum(a.values()) if a else None
        rp = rep.get((y, rid))
        ann.append([1470, y, rid, label[rid], lclean[rid], lkind[rid], istot[rid], s, len(a),
                    ";".join(str(x) for x in range(1, 13) if x not in a), rp,
                    (None if (s is None or rp is None) else s - rp), yearflag[y],
                    "Sum of monthly values from BPS WebAPI var 1470 (domain 0000); bps_reported_annual = period 'Tahunan' (13) if present"])
    write_csv(f"{EXTRACT}\\bps_arrivals_by_nationality_annual.csv",
              ["var_id", "year", "row_id", "row_label", "row_label_clean", "row_kind", "is_total_row", "sum_of_months_1_12", "n_months_with_value",
               "months_without_value", "bps_reported_annual_tahunan", "sum_minus_reported", "year_completeness_flag", "source"], ann)

    # ---- 331 + 1160 totals; 331 by country as bonus file
    tot = [r for r in data[331] if r["row_label_clean"] == "Jumlah"] + data[1160]
    write_csv(f"{EXTRACT}\\bps_tourism_receipts_total.csv", HDR, to_rows(tot))
    write_csv(f"{EXTRACT}\\bps_receipts_from_wisman_by_nationality_2000_2014.csv", HDR, to_rows(data[331]))

    # ---- 2195 outbound trips (all rows kept; total row flagged via is_total_row)
    write_csv(f"{EXTRACT}\\bps_outbound_trips.csv", HDR, to_rows(data[2195]))

    # ---- keyword search of variables
    kws = ["kebangsaan", "kunjungan wisatawan mancanegara", "wisatawan nasional", "negara tujuan",
           "negara tempat tinggal", "paspor", "pengeluaran wisatawan"]
    found = {}
    for kw in kws:
        base = "kw_var_" + re.sub(r"\W+", "_", kw)
        items, st = paged(f"list/model/var/domain/0000/keyword/{urllib.parse.quote(kw)}/", base)
        print(f"[kw var] {kw!r}: {len(items)} ({st})", flush=True)
        for it in items:
            f = found.setdefault(it["var_id"], dict(var_id=it["var_id"], title=it["title"], unit=it.get("unit"),
                                                     subject=it.get("sub_name"), keywords=[]))
            f["keywords"].append(kw)
    write_csv(f"{EXTRACT}\\bps_keyword_search_vars.csv", ["var_id", "title", "unit", "subject", "matched_keywords", "source"],
              [[f["var_id"], f["title"], f["unit"], f["subject"], "; ".join(f["keywords"]),
                "BPS WebAPI list/model/var keyword search, domain 0000"] for f in sorted(found.values(), key=lambda x: x["var_id"])])

    # ---- publication search + details (PDF links are resolved later by fetch_bps_pdfs.py)
    pkws = ["Statistik Pengeluaran Wisatawan Mancanegara", "Statistik Wisatawan Nasional",
            "Statistik Kunjungan Wisatawan Mancanegara", "Tourism Satellite Account"]
    pubs = {}
    for kw in pkws:
        base = "kw_pub_" + re.sub(r"\W+", "_", kw)
        items, st = paged(f"list/model/publication/domain/0000/lang/ind/keyword/{urllib.parse.quote(kw)}/", base)
        print(f"[kw pub] {kw!r}: {len(items)} ({st})", flush=True)
        for it in items:
            pubs[it["pub_id"]] = (it["title"], it.get("rl_date"), it.get("size"), kw)
    # explicit IDs from the task
    EXPLICIT = """7344d8c9b1935d342f2ff9e7 8f41f59ea24192828f6c7275 a14ac9b0d02a074aac856dfb 1aaafdb1eca4c2bdda880782
5d0ec91c10b00f0302bc6757 7bd0bd596f54cf0f51b45030 b88772d443001a23da1acf41
4fb8642851550952baead819 a85d584df19ea65a5e2b3d0b 0ba2b8f3f4f15dd18799f0c0 4dcc6b622ae0c4e7ea6a61e8 d79faad2c263388e94e160ee
ddea1823bc9cd63789d51b05 94ceb011540bd0cd73e3474c f2e676c8c2b7ae3346a28b88 77480cacdb0a39aba3de84ce 0873b4ec8f3645e62d8caa4c
27b61f56c20226ca8ecfd974""".split()
    rows = []
    for pid in sorted(set(EXPLICIT) | set(pubs)):
        d = api_json(f"view/domain/0000/model/publication/lang/ind/id/{pid}/", f"pub_{pid}.json", cache=CACHE)
        dd = d.get("data", {}) if d.get("data-availability") == "available" else {}
        rows.append([pid, dd.get("title"), dd.get("rl_date"), dd.get("size"), bool(dd.get("pdf")),
                     "task-listed" if pid in EXPLICIT else "found-by-search",
                     "BPS WebAPI view/model/publication"])
        print(f"[pub] {pid} {dd.get('title')} {dd.get('size')}", flush=True)
    write_csv(f"{EXTRACT}\\bps_publication_index.csv",
              ["pub_id", "title", "release_date", "size", "has_pdf_link", "origin", "source"], rows)

    # ---- metadata dump for the README
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_api_meta.json"), "w", encoding="utf-8") as f:
        json.dump(dict(metas={str(k): v for k, v in metas.items()}, yearflag={str(k): v for k, v in yearflag.items()}),
                  f, ensure_ascii=False, indent=1, default=str)
    # keep row-label dumps for the nationality map
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_vervar_labels.json"), "w", encoding="utf-8") as f:
        json.dump({str(k): [{"id": x["kode_ver_id"], "label": x["vervar"]} for x in vv] for k, vv in vervars.items()},
                  f, ensure_ascii=False)
    print("done")


if __name__ == "__main__":
    main()
