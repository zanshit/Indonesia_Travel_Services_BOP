"""Build 03_extract/hajj_umrah.csv from 02_raw/hajj_umrah (BPS API json + saved news/official pages).
Each figure is asserted against the saved page text. Run: python -X utf8 -I scripts/build_hajj_umrah.py
source_type: official = government statistic fetched from the publisher's own API/portal; official_via_news = a government/DPR/Kemenag
statement as quoted by a news outlet (primary document NOT retrieved); news = news-outlet compilation; industry = trade/market quote."""
import importlib.util, csv, json, glob, re, html as H
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
RAW = C.RAW / "hajj_umrah"
M = C._man(RAW)
COLS = ["year", "indicator", "value", "unit", "source", "url", "source_type", "retrieved_at", "note"]
out = []
_cache = {}


def page_text(fn):
    if fn not in _cache:
        h = (RAW / fn).read_text(encoding="utf-8", errors="ignore")
        h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
        _cache[fn] = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", h)))
    return _cache[fn]


def add(year, ind, val, unit, source, fn, stype, note="", assert_txt=None):
    if assert_txt:
        for a in ([assert_txt] if isinstance(assert_txt, str) else assert_txt):
            assert a in page_text(fn), (fn, a)
    m = M[fn]
    out.append(dict(year=year, indicator=ind, value=val, unit=unit, source=source, url=m["url"], source_type=stype,
                    retrieved_at=m["retrieved_at_utc"], note=note))


# ---------------------------------------------------------------- BPS var 178 (official; regular hajj through Kemenag)
for f in sorted(glob.glob(str(RAW / "bps_var178_data_th*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    fn = Path(f).name
    for k, v in d["datacontent"].items():
        if k.startswith("9999178"):
            y = int(k[len("9999178") + 1:-1]) + 1900
            add(y, "hajj_pilgrims_departed_regular_via_Kemenag", v, "persons",
                "BPS WebAPI var 178 'Jumlah Jemaah Haji yang Diberangkatkan ke Tanah Suci Mekah Menurut Provinsi' (national total, vervar 9999; source Ditjen PHU Kemenag)",
                fn, "official", "BPS series ends 2016 (no later years in API); 'Keberangkatan melalui Kementerian Agama' = regular hajj only, excludes special (khusus) hajj. URL shown without API key.")

# ---------------------------------------------------------------- quota (Kemenag figures as compiled by detik from kemenag.go.id)
Q = "detik_7965581_kuota_haji_2014_2025.html"
SRC_Q = "detikHikmah/detikSumut 2025-06-16 compiling Kemenag RI quota announcements"
QUOTA = {2015: (168800, 155200, 13600), 2016: (168800, 155200, 13600), 2017: (221000, 204000, 17000), 2018: (221000, 204000, 17000),
         2019: (231000, 214000, 17000), 2022: (100051, 92825, 7226), 2024: (241000, 213320, 27680), 2025: (221000, 203320, 17680)}
assertions = {2015: "168.800", 2017: "204.000", 2019: "214.000 jemaah reguler dan 17.000", 2022: "92.825 jemaah reguler dan 7.226", 2024: "213.320 jemaah reguler dan 27.680", 2025: "203.320 jemaah reguler dan 17.680"}
for y, (tot, reg, spc) in QUOTA.items():
    a = assertions.get(y) or assertions.get(y - 1)
    for ind, v in (("hajj_quota_total", tot), ("hajj_quota_regular", reg), ("hajj_quota_special", spc)):
        add(y, ind, v, "persons", SRC_Q, Q, "official_via_news",
            "Quota (not realised departures). " + ("2016 article detik 3212553 quotes special quota 13,000 rather than 13,600." if y == 2016 else ""), a)
add(2023, "hajj_quota_total", 229000, "persons", "Antara 2023-06-25 quoting Dirjen PHU Kemenag Hilman Latief (base 221,000 + 8,000 additional)",
    "antara_3606021_haji2023_realisasi_228093.html", "official_via_news", "", "229.000")
add(2023, "hajj_quota_regular", 210680, "persons", "Antara 2023-06-25 (base 203,320 + additional 7,360)", "antara_3606021_haji2023_realisasi_228093.html", "official_via_news", "derived sum 203,320+7,360", ["203.320", "7.360"])
add(2023, "hajj_quota_special", 18320, "persons", "Antara 2023-06-25 (base 17,680 + additional 640)", "antara_3606021_haji2023_realisasi_228093.html", "official_via_news", "derived sum 17,680+640", ["17.680", "640"])
add(2023, "hajj_pilgrims_departed_total", 228093, "persons", "Antara 2023-06-25 quoting Dirjen PHU Kemenag (realisation 99.6% of 229,000 quota)",
    "antara_3606021_haji2023_realisasi_228093.html", "official_via_news", "Only year with a realised-departure figure found beyond BPS 2015-16; regular+special", "228.093")
for y, fn in ((2020, "detik_7707774_kuota_2024_241000.html"), (2021, "detik_7707774_kuota_2024_241000.html")):
    add(y, "hajj_pilgrims_departed_total", 0, "persons", "detikHikmah 2024-12-29: KMA 494/2020 and KMA 660/2021 cancelled departures", fn, "official_via_news", "COVID cancellation", "tak ada jemaah haji yang berangkat")
add(2024, "hajj_quota_total_note", 241000, "persons", "Antara 2024 / detik 2024-12-29: 221,000 base + 20,000 additional from Saudi", "detik_7707774_kuota_2024_241000.html", "official_via_news",
    "Largest ever; allocation of the 20,000 additional quota is the subject of a KPK case (not examined here)", "241.000")

# ---------------------------------------------------------------- BPIH / Bipih / nilai manfaat
T = "detik_8186135_BPIH_2017_2026_table.html"
SRC_T = "detikHikmah 2025-10-30 'Statistik Biaya Haji 10 Tahun Terakhir' (compiled by detikcom from Keppres/Panja decisions)"
TABLE = {2017: (61.79, 34.89, 26.90), 2018: (68.96, 35.24, 33.72), 2019: (69.16, 35.24, 33.92), 2022: (97.79, 38.89, 57.91), 2023: (90.05, 49.81, 40.23), 2024: (93.4, 56.0, 37.3)}
for y, (b, p, n) in TABLE.items():
    a = f"BPIH {y} Rp {str(b).replace('.', ',')}"
    for ind, v in (("BPIH_avg_per_pilgrim_total_cost", b), ("Bipih_avg_paid_by_pilgrim", p), ("nilai_manfaat_avg_per_pilgrim", n)):
        add(y, ind, v * 1e6, "IDR per pilgrim (rounded to Rp 10,000 in source)", SRC_T, T, "news",
            "Regular hajj averages; source gives Rp million to 2 d.p.", a if y != 2017 else "BPIH 2017 Rp 61,79 juta")
# 2015, 2016 (pre-2017 regime: BPIH = amount paid by pilgrim)
add(2015, "BPIH_avg_per_pilgrim_USD", 2717, "USD per pilgrim", "detik 2015-05-27 (Perpres 64/2015; President Jokowi): average BPIH 1436H USD 2,717, down from USD 3,219",
    "detik_2926943_BPIH2015_perpres64.html", "official_via_news", "Pre-2017 regime: BPIH was paid by the pilgrim (no separate nilai manfaat subsidy in this figure)", ["2.717", "3.219"])
add(2016, "BPIH_avg_per_pilgrim", 34641304, "IDR per pilgrim", "detik 2016-05-17 Menag Lukman Hakim Saifuddin: average BPIH 2016 Rp34,641,304 (= USD 2,585)",
    "detik_3212553_BPIH2016.html", "official_via_news", "Pre-2017 regime; USD 2,585 at Rp13,400/USD", "34.641.304")
add(2016, "BPIH_avg_per_pilgrim_USD", 2585, "USD per pilgrim", "detik 2016-05-17 Menag", "detik_3212553_BPIH2016.html", "official_via_news", "", "2.585")
# exact figures
add(2024, "BPIH_avg_per_pilgrim_total_cost_exact", 93410286, "IDR per pilgrim", "Antara 2025-01 quoting Ketua Panja Abdul Wachid", "antara_4566750_panja_setujui_BPIH2025.html", "official_via_news", "", "93.410.286")
add(2024, "Bipih_avg_paid_by_pilgrim_exact", 56046171.60, "IDR per pilgrim", "Antara 2025-01 (PUI article quoting Panja)", "antara_4569022_PUI_BPIH2025_vs_2024.html", "official_via_news", "", "56.046.171,60")
for ind, v, a in (("BPIH_avg_per_pilgrim_total_cost_exact", 89410258.79, "89.410.258,79"), ("Bipih_avg_paid_by_pilgrim_exact", 55431750.78, "55.431.750,78"), ("nilai_manfaat_avg_per_pilgrim_exact", 33978508.01, "33.978.508,01")):
    add(2025, ind, v, "IDR per pilgrim", "Antara 2025-01 quoting Ketua Panja Biaya Haji Komisi VIII Abdul Wachid (Keppres 6/2025 averages)", "antara_4566750_panja_setujui_BPIH2025.html", "official_via_news",
        "Bipih = 62%, nilai manfaat = 38% of BPIH", a)
add(2025, "nilai_manfaat_total_regular", 6831820756658.34, "IDR", "detik 2025-02-13 on Keppres 6/2025", "detik_7776487_keppres6_2025_bipih_per_embarkasi.html", "official_via_news", "Total BPKH nilai manfaat for regular hajj 2025", "6.831.820.756.658,34")
for emb, v in (("Aceh", 46922333), ("Jakarta (Pondok Gede/Bekasi)", 58875751), ("Surabaya", 60955751), ("Makassar", 57670921)):
    add(2025, f"Bipih_per_embarkasi_{emb}", v, "IDR per pilgrim", "detik 2025-02-13 on Keppres 6/2025", "detik_7776487_keppres6_2025_bipih_per_embarkasi.html", "official_via_news",
        "Selected embarkasi; full list on the page. Bipih funds flight, part of Makkah/Madinah accommodation and living cost (per same page)", f"{v:,}".replace(",", "."))
for ind, v, a in (("BPIH_avg_per_pilgrim_total_cost_exact", 87409365.45, "87.409.365,45"), ("Bipih_avg_paid_by_pilgrim_exact", 54193806.58, "54.193.806,58"), ("nilai_manfaat_avg_per_pilgrim_exact", 33215558.87, "33.215.558,87")):
    add(2026, ind, v, "IDR per pilgrim", "detik 2025-10-30 on Panja decision 2025-10-29 (Keppres 34/2025 per Antara 2025-12-05)", T, "official_via_news", "Outside the 2015-2025 request; included for continuity", a)
add(2027, "BPIH_avg_per_pilgrim_total_cost_exact", 98466351.35, "IDR per pilgrim", "detik 2026-10-07 on DPR Panja conclusion read by Dasco", "detik_8697173_BPIH2027_komponen.html", "official_via_news", "Forward-looking decision (1448H/2027); context only", "98.466.351,35")

# ---------------------------------------------------------------- components
P25 = "antara_4565942_kemenag_usul_BPIH2025_89_67jt.html"
for comp, v, a in (("flight_embarkasi_Saudi_return", 34386390.68, "34.386.390,68"), ("accommodation_Makkah", 15232011.90, "15.232.011,90"), ("accommodation_Madinah", 4454403.48, "4.454.403,48"),
                   ("living_cost", 3200002.50, "3.200.002,50"), ("masyair_package_partial", 8099970.94, "8.099.970,94")):
    add(2025, f"Bipih_component_PROPOSAL_{comp}", v, "IDR per pilgrim", "Antara 2025-01-06 quoting Menag Nasaruddin Umar to Komisi VIII on 2024-12-30 (proposal; BPIH 93,389,684; Bipih 65,372,779)", P25, "official_via_news",
        "PROPOSAL, not the final Keppres 6/2025 split (final avg BPIH 89,410,258.79; component split of the final not found; DPR document berkas.dpr.go.id returned HTTP 403)", a)
add(2025, "Bipih_component_FINAL_flight_embarkasi_Saudi_return", 33100000, "IDR per pilgrim", "detik 2025-10-28: Panja chair says 2025 and 2026 flight cost is the same Rp33,100,000",
    "detik_8182587_bipih2026_komponen.html", "official_via_news", "", "33.100.000")
for comp, v, a in (("flight_embarkasi_Saudi_return", 33100000, "33.100.000"), ("accommodation_Makkah", 14652000, "14.652.000"), ("accommodation_Madinah", 3872000, "3.872.000"), ("living_cost", 3300000, "3.300.000")):
    add(2026, f"Bipih_component_PROPOSAL_{comp}", v, "IDR per pilgrim", "detik 2025-10-28 Government proposal to Panja (Bipih Rp54,924,000)", "detik_8182587_bipih2026_komponen.html", "official_via_news",
        "Government proposal before final Bipih 54,193,806.58; components sum to 54,924,000", a)
for comp, v, a in (("domestic_Indonesia_costs", 5643945.28, "5.643.945,28"), ("costs_in_Saudi_Arabia", 54317360.07, "54.317.360,07"), ("flight", 38505046, "38.505.046")):
    add(2027, f"BPIH_component_FINAL_{comp}", v, "IDR per pilgrim", "detik 2026-10-07 on DPR Panja conclusion (BPIH 98,466,351.35)", "detik_8697173_BPIH2027_komponen.html", "official_via_news",
        "The only full-BPIH three-way split found (domestic / in Saudi / flight); components sum to BPIH. Context for how much of BPIH is paid to Saudi-side providers", a)

# ---------------------------------------------------------------- umrah
add(2025, "umrah_pilgrims_from_Indonesia", 1600000, "persons (approx., 'sekitar 1,6 juta')", "Antara 2025 (BSI article) citing Siskopatuh 2025 data", "antara_5618112_BSI_siskopatuh2025_umrah_1_6jt.html", "official_via_news",
    "Siskopatuh = Kemenag/Kemenhaj umrah information system; figure quoted in a bank (BSI) context. No 2015-2024 umrah series found in this pass", "1,6 juta masyarakat Indonesia melaksanakan ibadah umrah")
add(2025, "umrah_reference_package_cost", 23000000, "IDR per pilgrim (minimum 'ideal' reference)", "detik 2025: KMA No. 1021/2023 on reference umrah cost (quoting Portal Informasi Indonesia / Kemenag)",
    "detik_7994597_umrah_biaya_2025_KMA1021_2023.html", "official_via_news",
    "Task brief cites KMA 777/2020 minimum Rp26 juta; the 2023 KMA 1021 reference of Rp23 juta is the later figure found (KMA 777/2020 itself not retrieved/verified)", "Rp 23 juta")
add(2025, "umrah_package_price_regular_range", "24-29 million", "IDR per pilgrim (9-11 days)", "detikHikmah 2025-10-30 market survey ('penelusuran detikHikmah')", "detik_8185474_umrah_mandiri_vs_travel_KMA1021.html", "industry",
    "Premium (Turkey/Dubai) 28-39 million; special (Ramadan/Friday) 32 to ~100 million; flight to Saudi ~Rp8 million one way", "Rp 24 juta hingga Rp 29 juta")
add(2025, "saudi_reported_foreign_umrah_visitors", 18030000, "persons (all nationalities)", "Saudi PEP Annual Report 2025 as reported by detikHikmah 2026-08-04", "detik_8603341_saudi_PEP_2025_umrah_18_03jt.html", "official_via_news",
    "Context: 18.03m umrah + 1.5m hajj pilgrims arrived from abroad in 2025; no Indonesia split in this article", "18,03 juta jemaah umrah")

with open(C.EXTRACT / "hajj_umrah.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(sorted(out, key=lambda d: (int(d["year"]), d["indicator"])))
print(len(out), "rows")
