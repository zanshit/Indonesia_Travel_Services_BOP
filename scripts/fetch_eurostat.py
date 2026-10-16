"""Fetch Eurostat bop_its6_det (partner = ID, Indonesia) via SDMX 2.1 SDMX-CSV.
Run: python -I scripts/fetch_eurostat.py [--refresh]
Outputs: 02_raw/eurostat/* + manifest.csv ; 03_extract/mirror_eurostat.csv, anchor_checks_eurostat.csv"""
import importlib.util
import sys
from collections import Counter
from pathlib import Path

_spec = importlib.util.spec_from_file_location("sdmx_common", Path(__file__).resolve().parent / "sdmx_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

REFRESH = "--refresh" in sys.argv
RAW = C.RAW / "eurostat"
BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/bop_its6_det/"
ITEMS = "SD+SDA+SDB+SDB1+SDB2+SDB3+SD1+SD2+SD3+SD4+SD5"
# key: freq.currency.bop_item.stk_flow.partner.geo
url_a = BASE + f"A.MIO_EUR.{ITEMS}.CRE+DEB+BAL.ID.?format=SDMX-CSV&startPeriod=2010"
url_q = BASE + "Q.MIO_EUR.SD.CRE+DEB+BAL.ID.?format=SDMX-CSV&startPeriod=2010"

paths = []
st, p = C.fetch(url_a, RAW, "bop_its6_det_annual_partner_ID.csv", refresh=REFRESH)
if st != 200:
    raise SystemExit(f"Eurostat annual fetch failed: HTTP {st}")
paths.append(p)
stq, pq = C.fetch(url_q, RAW, "bop_its6_det_quarterly_SD_partner_ID.csv", refresh=REFRESH)
if stq == 200:
    paths.append(pq)
else:
    print(f"  quarterly not available (HTTP {stq}) - recorded in manifest", flush=True)
man = C.load_manifest(RAW)

# Eurostat geo code -> (ISO3 or aggregate code, name)
GEO = {"AL": ("ALB", "Albania"), "AT": ("AUT", "Austria"), "BA": ("BIH", "Bosnia and Herzegovina"),
       "BE": ("BEL", "Belgium"), "BG": ("BGR", "Bulgaria"), "CH": ("CHE", "Switzerland"),
       "CY": ("CYP", "Cyprus"), "CZ": ("CZE", "Czechia"), "DE": ("DEU", "Germany"),
       "DK": ("DNK", "Denmark"), "EE": ("EST", "Estonia"), "EL": ("GRC", "Greece"),
       "ES": ("ESP", "Spain"), "EU27_2020": ("EU27_2020", "European Union (27 countries, from 2020)"),
       "FI": ("FIN", "Finland"), "FR": ("FRA", "France"), "HR": ("HRV", "Croatia"),
       "HU": ("HUN", "Hungary"), "IE": ("IRL", "Ireland"), "IS": ("ISL", "Iceland"),
       "IT": ("ITA", "Italy"), "LT": ("LTU", "Lithuania"), "LU": ("LUX", "Luxembourg"),
       "LV": ("LVA", "Latvia"), "ME": ("MNE", "Montenegro"), "MT": ("MLT", "Malta"),
       "NL": ("NLD", "Netherlands"), "NO": ("NOR", "Norway"), "PL": ("POL", "Poland"),
       "PT": ("PRT", "Portugal"), "RO": ("ROU", "Romania"), "RS": ("SRB", "Serbia"),
       "SE": ("SWE", "Sweden"), "SI": ("SVN", "Slovenia"), "SK": ("SVK", "Slovakia"),
       "TR": ("TUR", "Turkiye"), "UK": ("GBR", "United Kingdom"), "XK": ("XKX", "Kosovo")}
LABEL = {"SD": "Travel", "SDA": "Travel; Business", "SDB": "Travel; Personal",
         "SDB1": "Travel; Personal; Health-related", "SDB2": "Travel; Personal; Education-related",
         "SDB3": "Travel; Personal; Other than health-related and education-related",
         "SD1": "Travel; Goods", "SD2": "Travel; Local transport services",
         "SD3": "Travel; Accommodation services", "SD4": "Travel; Food-serving services",
         "SD5": "Travel; Other services"}   # labels as in the OECD DSD codelist (Eurostat CSV carries codes only)
OUT = {"CRE": "debit", "DEB": "credit", "BAL": "balance"}   # reporter flow -> Indonesia flow (flipped)

rows, seen, unmapped = [], set(), set()
for pth in paths:
    m = man[pth.name]
    for r in C.read_csv_rows(pth):
        assert r["partner"] == "ID" and r["currency"] == "MIO_EUR", r
        g = r["geo"]
        if g not in GEO:
            unmapped.add(g)
        iso, nm = GEO.get(g, (g, g))
        y, q = C.split_period(r["TIME_PERIOD"])
        flow = OUT[r["stk_flow"]]
        val = C.neg(r["OBS_VALUE"]) if flow == "balance" else r["OBS_VALUE"]
        key = (g, r["bop_item"], r["stk_flow"], r["TIME_PERIOD"], r["freq"])
        assert key not in seen, key
        seen.add(key)
        flags = "|".join(x for x in (r.get("OBS_FLAG", ""), ("conf:" + r["CONF_STATUS"]) if r.get("CONF_STATUS") else "") if x)
        rows.append({
            "source": "Eurostat bop_its6_det", "line": "B_mirror", "reporter": iso,
            "partner_iso3": "IDN", "partner_name": "Indonesia", "flow_idn": flow,
            "item": r["bop_item"], "item_label": LABEL.get(r["bop_item"], ""), "year": y, "quarter": q,
            "value": val, "currency": "EUR", "unit_mult": "6", "adjustment": "",
            "methodology_type": "", "obs_status": flags, "url": m["url"], "retrieved_at": m["retrieved_at_utc"],
            "_reporter_name": nm})
assert not unmapped, unmapped
C.write_tidy(C.EXTRACT / "mirror_eurostat.csv", rows)

def A(flow, exp, name):
    return dict(name=name, expected=exp, filt=dict(reporter="EU27_2020", flow_idn=flow, item="SD", year="2023", quarter=""))
anchors = [
    A("credit", "1829.8", "Eurostat EU27 SD 2023: reporter DEB 1829.8 -> IDN credit"),
    A("debit", "351.9", "Eurostat EU27 SD 2023: reporter CRE 351.9 -> IDN debit"),
    A("balance", "1477.9", "Eurostat EU27 SD 2023: reporter BAL -1477.9 -> IDN balance +1477.9"),
]
res = C.check_anchors(rows, anchors, C.EXTRACT / "anchor_checks_eurostat.csv")
print("DONE mirror_eurostat.csv rows:", len(rows), "anchors:", Counter(r["status"] for r in res))
