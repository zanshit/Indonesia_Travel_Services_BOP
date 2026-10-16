"""Data loaders for the travel balance workbook (imported by build_excel.py).

Run:  python -I scripts/build_excel.py   (from the project root or anywhere)
Reads 03_extract/*.csv and 02_raw/fx/wb_PA.NUS.FCRF.json; writes output/*.xlsx,
03_extract/best_estimate_2024.csv and 04_qa/reconciliation.md.
"""
import json
import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "03_extract"
OUT = ROOT / "output" / "Neraca_Jasa_Perjalanan_Indonesia_per_Negara.xlsx"
YEAR = 2024

NAVY, ACCENT, GREY, LIGHT = "051C2C", "2251FF", "A2AAAD", "F2F2F2"
FONT = "Arial"
NUM = '#,##0.0;(#,##0.0);"–"'
NUM0 = '#,##0;(#,##0);"–"'

LINKS = {
    "OECD TIS": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BOP@DF_TIS,1.0/.IDN.SD...A.USD_EXC.?startPeriod=2019&format=csvfilewithlabels",
    "Eurostat": "https://ec.europa.eu/eurostat/databrowser/view/bop_its6_det/default/table?lang=en",
    "ABS": "https://www.abs.gov.au/statistics/economy/international-trade/international-trade-supplementary-information-calendar-year/latest-release",
    "BaTIS": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BATIS@DF_BATIS,1.0/IDN..X+M.S.SD.A.USD_EXC.B?startPeriod=2019&format=csvfilewithlabels",
    "BaTIS metodologi": "https://www.wto.org/english/res_e/statis_e/daily_update_e/OECD-WTO_Batis_methodology_BPM6.pdf",
    "BPS kredit": "https://www.bps.go.id/id/statistics-table/2/MjcyIzI=/rata-rata-pengeluaran-wisatawan-mancanegara-per-kunjungan-menurut-negara-tempat-tinggal.html",
    "BPS debit": "https://www.bps.go.id/id/publication/2026/04/30/7344d8c9b1935d342f2ff9e7/statistik-wisatawan-nasional-2025.html",
    "BI": "https://www.bi.go.id/SEKI/tabel/TABEL5_3.xls",
    "Tourism Malaysia": "https://data.tourism.gov.my/frontend/pdf/Malaysia_Tourist_Profile_2024%20v2.pdf",
    "STB": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/record-singapore-tourism-receipts-from-january-to-september-2025/",
    "JTA": "https://www.mlit.go.jp/kankocho/",
    "MOTS": "https://www.mots.go.th/",
    "Haji": "https://berkas.dpr.go.id/akd/dokumen/komisi8-14-9c99c60e776a2177daf06668e4910509.pdf",
    "World Bank kurs": "https://data.worldbank.org/indicator/PA.NUS.FCRF",
}

NAMA = {
    "AUS": "Australia", "MYS": "Malaysia", "SGP": "Singapura", "CHN": "Tiongkok", "JPN": "Jepang",
    "KOR": "Korea Selatan", "USA": "Amerika Serikat", "GBR": "Inggris", "IND": "India", "SAU": "Arab Saudi",
    "THA": "Thailand", "VNM": "Vietnam", "PHL": "Filipina", "BRN": "Brunei Darussalam", "MMR": "Myanmar",
    "HKG": "Hong Kong", "TWN": "Taiwan", "TLS": "Timor-Leste", "ARE": "Uni Emirat Arab", "EGY": "Mesir",
    "DEU": "Jerman", "FRA": "Prancis", "NLD": "Belanda", "ITA": "Italia", "ESP": "Spanyol", "CHE": "Swiss",
    "RUS": "Rusia", "CAN": "Kanada", "NZL": "Selandia Baru", "BEL": "Belgia", "AUT": "Austria",
    "DNK": "Denmark", "SWE": "Swedia", "NOR": "Norwegia", "FIN": "Finlandia", "POL": "Polandia",
    "CZE": "Ceko", "HUN": "Hungaria", "PRT": "Portugal", "IRL": "Irlandia", "GRC": "Yunani", "TUR": "Turki",
    "PAK": "Pakistan", "BGD": "Bangladesh", "LKA": "Sri Lanka", "ISR": "Israel", "LUX": "Luksemburg",
    "ROU": "Rumania", "BGR": "Bulgaria", "HRV": "Kroasia", "SVK": "Slowakia", "SVN": "Slovenia",
    "EST": "Estonia", "LVA": "Latvia", "LTU": "Lituania", "ISL": "Islandia", "ARG": "Argentina",
    "BRA": "Brasil", "MEX": "Meksiko", "ZAF": "Afrika Selatan", "PNG": "Papua Nugini", "KWT": "Kuwait",
    "YEM": "Yaman", "QAT": "Qatar", "OMN": "Oman", "KHM": "Kamboja", "LAO": "Laos", "MAC": "Makau",
    "CYP": "Siprus", "MLT": "Malta", "ALB": "Albania", "SRB": "Serbia", "BIH": "Bosnia dan Herzegovina",
    "MNE": "Montenegro", "XKX": "Kosovo", "IRN": "Iran", "IRQ": "Irak", "JOR": "Yordania", "NPL": "Nepal",
}

# ---------------------------------------------------------------- helpers
def nama(iso, fallback=None):
    if iso in NAMA:
        return NAMA[iso]
    if fallback and isinstance(fallback, str):
        return fallback.replace("â€™", "'").replace("�", "'").split(" (")[0]
    return iso


def fx():
    d = json.loads((ROOT / "02_raw" / "fx" / "wb_PA.NUS.FCRF.json").read_text(encoding="utf-8"))[1]
    out = {}
    for r in d:
        if r["value"] is not None:
            out[(r["countryiso3code"], int(r["date"]))] = r["value"]
    return out


FX = fx()


def to_usd(value, ccy_country, year):
    """value in local currency (millions) -> USD millions, World Bank LCU per USD period average."""
    return value / FX[(ccy_country, year)]


def pivot_cdb(df, key):
    p = df.pivot_table(index=key, columns="flow_idn", values="value", aggfunc="sum")
    for c in ("credit", "debit", "balance"):
        if c not in p:
            p[c] = float("nan")
    p["balance"] = p["balance"].where(p["balance"].notna(), p["credit"] - p["debit"])
    return p[["credit", "debit", "balance"]]


# ---------------------------------------------------------------- data: mirrors
def load_oecd_tis():
    t = pd.read_csv(EX / "mirror_oecd_tis.csv", low_memory=False)
    t = t[(t.currency == "USD") & (t["item"] == "SD") & (t.reporter != "EU27_2020")]
    return t


def load_eurostat():
    e = pd.read_csv(EX / "mirror_eurostat.csv", low_memory=False)
    e = e[(e["item"] == "SD") & (e.reporter != "EU27_2020")].copy()
    e["value_usd"] = [v / FX[("EMU", y)] if pd.notna(v) and ("EMU", y) in FX else float("nan")
                      for v, y in zip(e.value, e.year)]
    return e


def load_abs():
    a = pd.read_csv(EX / "mirror_abs.csv")
    a = a[a.source.str.contains(r"Tables? [78]\.", regex=True)]
    a["value_usd"] = [v / FX[("AUS", y)] if ("AUS", y) in FX else float("nan") for v, y in zip(a.value, a.year)]
    return a


# ---------------------------------------------------------------- data: BaTIS
def load_batis():
    b = pd.read_csv(EX / "batis.csv", low_memory=False)
    return b[(b["item"] == "SD")]


def batis_year(b, year):
    own = b[(b.line == "A_model") & (b.year == year) & (b.partner_iso3 != "W")]
    rows = {}
    for adj in ("F", "B"):
        p = own[own.adjustment.str.startswith(adj)].pivot_table(index="partner_iso3", columns="flow_idn",
                                                                values="value", aggfunc="sum")
        rows[adj] = p
    meth = (own[own.adjustment.str.startswith("F")].groupby("partner_iso3").methodology_type
            .agg(lambda s: "/".join(sorted(set(str(x).split(":")[0] for x in s.dropna())))))
    names = own.groupby("partner_iso3").partner_name.first()
    side = b[(b.line == "A_model_partnerside") & (b.year == year) & (b.adjustment.str.startswith("N"))]
    mirror = side.pivot_table(index="reporter", columns="flow_idn", values="value", aggfunc="sum")
    df = pd.DataFrame({
        "kredit_F": rows["F"].get("credit"), "kredit_mitra": mirror.get("credit"), "kredit_B": rows["B"].get("credit"),
        "debit_F": rows["F"].get("debit"), "debit_mitra": mirror.get("debit"), "debit_B": rows["B"].get("debit"),
    })
    df = df.reindex(rows["B"].index)
    df["neraca_B"] = df.kredit_B - df.debit_B
    df["metode"] = meth.reindex(df.index)
    df["nama"] = [nama(i, names.get(i)) for i in df.index]
    return df


# ---------------------------------------------------------------- data: BPS reconstruction
SHARE_MAP = [  # (pattern on lowercase label, iso3 or None for residual, spend group key)
    (r"^malaysia", "MYS", "malaysia"), (r"^singapura", "SGP", "singapura"), (r"^thailand", "THA", "thailand"),
    (r"^vietnam", "VNM", "vietnam"), (r"^filipina", "PHL", "asean lainnya"), (r"^brunei", "BRN", "asean lainnya"),
    (r"^myanmar", "MMR", "asean lainnya"), (r"^kamboja", "KHM", "asean lainnya"),
    (r"^asean lainnya", None, "asean lainnya"),
    (r"tiongkok|people", "CHN", "tiongkok"), (r"^jepang", "JPN", "jepang"), (r"^korea selatan", "KOR", "korea selatan"),
    (r"^hong kong", "HKG", "hong kong"), (r"^taiwan", "TWN", "asia lainnya"), (r"^india", "IND", "asia lainnya"),
    (r"^timor", "TLS", "asia lainnya"), (r"^asia lainnya", None, "asia lainnya"),
    (r"^arab saudi", "SAU", "arab saudi"), (r"^uni emirat", "ARE", "timur tengah lainnya"),
    (r"^mesir", "EGY", "timur tengah lainnya"), (r"^yaman", "YEM", "timur tengah lainnya"),
    (r"^kuwait", "KWT", "timur tengah lainnya"), (r"^turki", "TUR", "eropa"),
    (r"^timur tengah lainnya", None, "timur tengah lainnya"),
    (r"^inggris", "GBR", "eropa"), (r"^belanda", "NLD", "eropa"), (r"^perancis", "FRA", "eropa"),
    (r"^jerman", "DEU", "eropa"), (r"^rusia", "RUS", "eropa"), (r"^eropa lainnya", None, "eropa"),
    (r"^amerika serikat", "USA", "amerika serikat"), (r"^kanada", "CAN", "lainnya"), (r"^meksiko", "MEX", "lainnya"),
    (r"^brazil", "BRA", "lainnya"), (r"^amerika lainnya", None, "lainnya"), (r"^australia", "AUS", "australia"),
    (r"^selandia baru", "NZL", "lainnya"), (r"^papua", "PNG", "lainnya"), (r"^oseania lainnya", None, "lainnya"),
    (r"^afrika selatan", "ZAF", "lainnya"), (r"^afrika lainnya", None, "lainnya"),
]
OWN_SPEND = {"MYS": "malaysia", "SGP": "singapura", "THA": "thailand", "VNM": "vietnam", "HKG": "hong kong",
             "JPN": "jepang", "KOR": "korea selatan", "CHN": "tiongkok", "SAU": "arab saudi",
             "USA": "amerika serikat", "AUS": "australia"}
SPEND_KEYS = {"malaysia": r"^malaysia", "singapura": r"^singapura", "thailand": r"^thailand", "vietnam": r"^vietnam",
              "asean lainnya": r"^asean lainnya", "hong kong": r"^hong kong", "jepang": r"^jepang",
              "korea selatan": r"^korea selatan", "tiongkok": r"tiongkok|people", "asia lainnya": r"^asia lainnya",
              "arab saudi": r"^arab saudi", "timur tengah lainnya": r"^timur tengah lainnya",
              "amerika serikat": r"^amerika serikat", "australia": r"^australia", "eropa": r"^eropa/|^eropa$",
              "lainnya": r"^lainnya"}


def bps_credit(year):
    m = pd.read_csv(EX / "bps_nationality_rows.csv")
    s = pd.read_csv(EX / "bps_spend_per_visit_by_nationality.csv")
    a = pd.read_csv(EX / "bps_arrivals_by_nationality_annual.csv")
    s = s[s.year == year]
    a = a[(a.year == year)]
    spend = dict(zip(s.row_label_clean, s.value))
    arr = a[a.row_kind == "country_or_entity"]
    arr_by = dict(zip(arr.row_label_clean, arr.bps_reported_annual_tahunan.fillna(arr.sum_of_months_1_12)))
    total_arr = a[a.is_total_row].bps_reported_annual_tahunan.max()
    rows = []
    for _, r in m[m.var272_label.notna() & m.iso3.notna()].iterrows():
        sp = spend.get(r.var272_label)
        ar = arr_by.get(r.var1470_label)
        if sp is None or ar is None:
            continue
        rows.append({"iso3": r.iso3, "nama": nama(r.iso3, r.canonical_name_en), "kunjungan": ar,
                     "pengeluaran_per_kunjungan": sp})
    df = pd.DataFrame(rows).set_index("iso3")
    other_spend = spend.get("Negara lainnya")
    resid_arr = total_arr - df.kunjungan.sum()
    return df, {"total_kunjungan": total_arr, "sisa_kunjungan": resid_arr, "pengeluaran_negara_lainnya": other_spend,
                "rata_rata": spend.get("Rata- Rata") or spend.get("Rata-Rata")}


def bps_debit(year):
    o = pd.read_csv(EX / "bps_outbound_by_destination.csv")
    sh = o[(o.year == year) & (o.figure_or_table_id == "Lampiran 4") & (o.measure == "trip_share_pct")]
    sh = sh[sh.edition == sh.edition.max()]
    sp = o[(o.year == year) & (o.figure_or_table_id == "Lampiran 20") & (o.purpose == "Total")]
    sp = sp[sp.edition == sp.edition.max()]
    spend = {}
    for key, pat in SPEND_KEYS.items():
        hit = sp[sp.destination.str.lower().str.contains(pat, regex=True)]
        if len(hit):
            spend[key] = float(hit.value.iloc[0])
    trips_df = pd.read_csv(EX / "bps_outbound_trips.csv")
    trips = float(trips_df[(trips_df.year == year) & (trips_df.row_label == "Jumlah") &
                           (trips_df.period_label == "Tahunan")].value.iloc[0])
    rows, resid = [], []
    for _, r in sh.iterrows():
        lab = str(r.destination).lower().strip()
        for pat, iso, grp in SHARE_MAP:
            if re.search(pat, lab):
                entry = {"label": r.destination, "pangsa_pct": r.value, "kelompok_pengeluaran": grp,
                         "pengeluaran_per_perjalanan": spend.get(grp),
                         "sumber_pengeluaran": "rata-rata negara" if OWN_SPEND.get(iso) == grp
                         else "rata-rata kelompok"}
                if iso:
                    entry.update(iso3=iso, nama=nama(iso))
                    rows.append(entry)
                else:
                    resid.append(entry)
                break
    df = pd.DataFrame(rows).drop_duplicates("iso3").set_index("iso3")
    total_spend = sp[sp.destination == "Total"].value.iloc[0]
    return df, pd.DataFrame(resid), {"total_perjalanan": trips, "rata_rata": float(total_spend), "spend": spend}


# ---------------------------------------------------------------- data: destination side
def destination_side(year):
    d = pd.read_csv(EX / "destination_side.csv")
    d = d[d.year == year]
    g = lambda iso, ind: d[(d.destination_iso3 == iso) & (d.indicator == ind)].value
    rows = []
    v = g("MYS", "receipts_from_indonesia")
    air = g("MYS", "intl_airfare_share_of_expenditure")
    if len(v):
        share = float(air.iloc[0]) / 100 if len(air) else 0
        rows.append({"iso3": "MYS", "nama": "Malaysia", "nilai_lokal": float(v.iloc[0]), "mata_uang": "MYR juta",
                     "debit_usd": to_usd(float(v.iloc[0]) * (1 - share), "MYS", year), "periode": "Jan–Des",
                     "catatan": f"Tiket pesawat internasional ({share:.1%}) dikeluarkan", "sumber": "Tourism Malaysia"})
    v = g("SGP", "receipts_from_indonesia")
    if len(v):
        rows.append({"iso3": "SGP", "nama": "Singapura", "nilai_lokal": float(v.iloc[0]), "mata_uang": "SGD juta",
                     "debit_usd": to_usd(float(v.iloc[0]), "SGP", year), "periode": "Jan–Sep",
                     "catatan": "Hanya Jan–Sep; tanpa wisata, hiburan & judi", "sumber": "STB"})
    v = g("JPN", "receipts_from_indonesia")
    if len(v):
        rows.append({"iso3": "JPN", "nama": "Jepang", "nilai_lokal": float(v.iloc[0]) * 100, "mata_uang": "JPY juta",
                     "debit_usd": to_usd(float(v.iloc[0]) * 100, "JPN", year), "periode": "Jan–Des",
                     "catatan": "", "sumber": "JTA"})
    v = g("THA", "receipts_from_indonesia_usd")
    vl = g("THA", "receipts_from_indonesia")
    if len(v):
        rows.append({"iso3": "THA", "nama": "Thailand", "nilai_lokal": float(vl.iloc[0]) if len(vl) else None,
                     "mata_uang": "THB juta", "debit_usd": float(v.iloc[0]), "periode": "Jan–Des",
                     "catatan": "USD sesuai publikasi MOTS", "sumber": "MOTS"})
    h = pd.read_csv(EX / "hajj_umrah.csv")
    h = h[h.year == year]
    q = h[h.indicator == "hajj_quota_total"].value
    c = h[h.indicator == "BPIH_avg_per_pilgrim_total_cost_exact"].value
    hf = pd.read_csv(EX / "hajj_umrah.csv")
    flight = hf[hf.indicator == "Bipih_component_FINAL_flight_embarkasi_Saudi_return"].value
    if len(q) and len(c) and len(flight):
        per = float(c.iloc[0]) - float(flight.iloc[0])
        idr = float(q.iloc[0]) * per / 1e6
        rows.append({"iso3": "SAU", "nama": "Arab Saudi", "nilai_lokal": idr, "mata_uang": "IDR juta",
                     "debit_usd": to_usd(idr, "IDN", year), "periode": "Musim haji",
                     "catatan": "Haji saja (kuota × biaya di luar tiket); umrah tidak tersedia", "sumber": "Haji"})
    return pd.DataFrame(rows).set_index("iso3")


