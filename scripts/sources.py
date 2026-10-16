"""Source registry for the workbook: for every source, (1) a page to browse the data / find the download
menu and (2) a link that downloads the data file directly.

Every URL here was opened on 2026-10-16 (see 04_qa/link_check.csv, written by scripts/check_links.py).
BPS PDF links are the official webapi.bps.go.id/download.php links that the BPS WebAPI returns for each
publication; they download without an API key. bps.go.id pages sit behind a Cloudflare bot check, so they
open in a normal browser but cannot be tested automatically."""

BPS_PENGELUARAN_2024 = "https://webapi.bps.go.id/download.php?f=/brduwku1DSgOYdICEs25HN5Um1sSHNKQUZKUVByUW43TEdGSmpLcU1pWjQrWkVyODM1ZW1SWHJ1YWM3elJ0VmpMSXQ0K3AxaXdMY0ZDUElzdDVGZVUwWUFRYnl5ZUxlVFc4Nnh5c3NZY3lsRkk1dHd0N3M2Z0hhRmRWNEp5QzZQQ0h4bVpsNmFCMEZNTEE1T1ZDSGhqR3oySDFPUWU2NWNzUEFpQ0dIRmtvT0tUa3N3RnB0eG9iSWZ0dUIwVi9HaTJoRGc1cWtwRnRLeS9DZER2SytoV0FYanhKYkNVYzI5OUVOWE4vV05Bakk2TTR5dDkwSWlKZU9BL3NFSSszZERRYnQvQVFnSzJuTmpUQ2VKKzNaSG9RRlZxdGVVd24yY3dVSjh3PT0="
BPS_KUNJUNGAN_2024 = "https://webapi.bps.go.id/download.php?f=rEB9s/sAcyKXn36czAQSWUpraWhxaURwZ2JPejYybHRIMm9aNElybWwwRUR1Q0Fxc3ZiU25GUUl5L0ptaGpMTHF1SzN1Z3NnemUySkw1MUVIdW96WFAyVS9jTFNUM1hCOS9OUWtLekhGdGJZOG4yT1BwK2F6dWFUTkNudUJWcWtrcE5LbE83ZmFiQkxDNHNCQjNMaUkyS2tQR0lUUkhkZzA1STRGVlNDWVdtS3YwSS9leTQ0ZzJ4VENlQU9xYkpXRy9wLzVJTFlzZkh2SFRBVVdjbm45L2d5YlprYWtiL0FHV2FDOXZ5SnZFUDFKdWcvcDhtMmk3aHFXdTlMbGFpZ1A1Vi9vZDdMZnliTFZScERYSjE0KytMb0ZrbnhRNHcrNi80V3pRPT0="
BPS_SWN_2025 = "https://webapi.bps.go.id/download.php?f=ExlK6XbY6OnXADZQ8UNZYkQyOWtQUFFod0Y5Q1BwZFkzSFJZelBXYkQrL2ZXTHV2ZERSemVzTzM0YVpNdXN5RlZGeWdoRGp6ZVVkOURTaG1nVE8vVG0zYlhhVTdWOGVPYzR4RVJTdGZWRElsUnlOWFl6bXgzL25QenFMTDNpQ04xUXRaYjBRTmhkZlBVMDJzYWN1b3BJbzJiaXNId0VzZUI0VUMvSWNJNy9DbkVkajNWa0NzSFBkWWthOUpXRjBpR0tRK05KNm1ZOGpDa3NqQkYrLy96d2J3SkdKZzdHb3NreDBWMC9CQU9hUFFTVWNUM2JiZUJXa3VuQkRlTGR0cnBRZ29iVHRKMGxRVUtlYUY="
BPS_SWN_2024 = "https://webapi.bps.go.id/download.php?f=zsX0nmeR2GLmYyC5idnuVVVPYU1Yb1pSTktGVXJxZWwvNE5qaWpBZVEzdGREQUNEbFlKUWlhUXpqcEFMWUVHd0UzaVFibjZkY2pUNi9yQVhhM3JLa2wvcXd1V29Ia1U0Y1U4SnA5d0VWQmpNV3FkTTVvR0Q3NW1zWTlCbFZuVzhVS0pvdFdJT25uak9CWThVNjNLY2trc3NiRzJmcndSUkE5dHBvT2R4TFFodVhXdktlT2c1RE1YRHpWMS9oSVhpSlhPb2ZyWVBlR3lkMFJxYXlJOWZzWWl1V0FCUFE0YXVSdnpBZ282MHVwZmtEYlVWdllESHBqMkVNZk55eVVtWSt0bm9ibWtQQWY4M3g4TzE="
BPS_TSA = "https://webapi.bps.go.id/download.php?f=ubF8LEhfIXUT7L5EIjGv6W10OFZCdTcxVTZYeU1VZGV3YS8yc1hRU25NNHpCYTNBTU50SExGWFBuN1hFMXU0YXdxZ1VCcDV6QmFiUFBsNnQvRDl1TE1ORTh1TjgzL3k5L1NVQnovSlZGdlJ2SENRd3hlYmE2eFdzWmROT0ZmeG8rd3BPRHdDeXA0cElVK3NMMHV0OGNyZEQzSGtRTmJVWW9NbjdZZk1LUmZzRkVHbVNTVjY1ZThmMXoxWkRLdFlFQjBkN0YzQWYvRVZuZXp0aDAxS2RxaGtHWlQ0bFNYeEZOMC8rMkVuK1VyVVBNY2ZDQyt6NzBXeGZFMktNQlhVanJRd1FsM2xsdnVhRlE4bzBkSmo4cTBqWlh3OGJkUDUrU3VsY2hRPT0="
BPS_NOTE = "Halaman bps.go.id memakai verifikasi anti-bot; di browser biasa terbuka normal setelah beberapa detik."


def bps_pub(date, pub_id):
    return f"https://www.bps.go.id/id/publication/{date}/{pub_id}"


def bps_table(code, slug):
    return f"https://www.bps.go.id/id/statistics-table/2/{code}/{slug}.html"


# key -> label, browse [(text, url)], unduh [(text, url)], catatan
SRC = {
    "BPS_KREDIT_PENGELUARAN": dict(
        label="BPS: pengeluaran wisman per kunjungan menurut negara (var 272)",
        browse=[("Tabel BPS var 272", bps_table(
            "MjcyIzI=", "rata-rata-pengeluaran-wisatawan-mancanegara-per-kunjungan-menurut-negara-tempat-tinggal"))],
        unduh=[("PDF Statistik Pengeluaran Wisman 2024", BPS_PENGELUARAN_2024)], catatan=BPS_NOTE),
    "BPS_KREDIT_KUNJUNGAN": dict(
        label="BPS: kunjungan wisman menurut paspor (var 1470)",
        browse=[("Tabel BPS var 1470", bps_table(
            "MTQ3MCMy", "jumlah-kunjungan-wisatawan-mancanegara-per-bulan-menurut-paspor-yang-dipegang"))],
        unduh=[("PDF Statistik Kunjungan Wisman 2024", BPS_KUNJUNGAN_2024)], catatan=BPS_NOTE),
    "BPS_DEBIT_PANGSA": dict(
        label="BPS Statistik Wisatawan Nasional 2025, Lampiran 4 (pangsa negara tujuan 2024)",
        browse=[("Halaman publikasi BPS", bps_pub("2026/04/30", "7344d8c9b1935d342f2ff9e7"))],
        unduh=[("PDF Statistik Wisatawan Nasional 2025", BPS_SWN_2025)], catatan=BPS_NOTE),
    "BPS_DEBIT_PENGELUARAN": dict(
        label="BPS Statistik Wisatawan Nasional 2024, Lampiran 20 (pengeluaran per perjalanan 2024)",
        browse=[("Halaman publikasi BPS", bps_pub("2025/03/17", "8f41f59ea24192828f6c7275"))],
        unduh=[("PDF Statistik Wisatawan Nasional 2024", BPS_SWN_2024)], catatan=BPS_NOTE),
    "BPS_SWN": dict(
        label="BPS Statistik Wisatawan Nasional 2025 (Lampiran 4) dan 2024 (Lampiran 20)",
        browse=[("Publikasi SWN 2025", bps_pub("2026/04/30", "7344d8c9b1935d342f2ff9e7")),
                ("Publikasi SWN 2024", bps_pub("2025/03/17", "8f41f59ea24192828f6c7275"))],
        unduh=[("PDF SWN 2025", BPS_SWN_2025), ("PDF SWN 2024", BPS_SWN_2024)], catatan=BPS_NOTE),
    "BPS_PERJALANAN": dict(
        label="BPS: jumlah perjalanan wisatawan nasional (var 2195)",
        browse=[("Tabel BPS var 2195", bps_table("MjE5NSMy", "jumlah-perjalanan-wisatawan-nasional"))],
        unduh=[("PDF Statistik Wisatawan Nasional 2025", BPS_SWN_2025)], catatan=BPS_NOTE),
    "BPS_TSA": dict(
        label="BPS Tourism Satellite Account 2023–2025",
        browse=[("Halaman publikasi BPS", bps_pub("2026/09/01", "27b61f56c20226ca8ecfd974"))],
        unduh=[("PDF TSA 2023–2025", BPS_TSA)], catatan=BPS_NOTE),
    "PES": dict(
        label="Kemenpar: Passenger Exit Survey (PES)",
        browse=[("Halaman publikasi PES (Kemenpar)", "https://kemenpar.go.id/publikasi-passenger-exit-survey")],
        unduh=[("PDF PES 2014", "https://api.kemenpar.go.id/storage/app/resources/PES%202014rev.pdf")],
        catatan="Alamat lama api2.kemenparekraf.go.id sudah mati; diganti domain baru kemenpar.go.id."),
    "KEMENPAR": dict(
        label="Kemenpar: statistik jasa perjalanan / devisa pariwisata",
        browse=[("Statistik jasa perjalanan", "https://kemenpar.go.id/statistik-jasa-perjalanan"),
                ("Statistik devisa pariwisata", "https://kemenpar.go.id/statistik-devisa-pariwisata")],
        unduh=[("PDF Neraca Jasa Perjalanan 2010–2016", "https://api.kemenpar.go.id/storage/app/resources/NPI.pdf")]),
    "OECD_TIS": dict(
        label="OECD International Trade in Services (TIS)",
        browse=[("OECD Data Explorer", "https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ"
                 "&df[id]=DSD_BOP%40DF_TIS&df[ag]=OECD.SDD.TPS")],
        unduh=[("CSV mitra = Indonesia", "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BOP@DF_TIS,1.0/"
                ".IDN.SD...A.USD_EXC.?startPeriod=2019&format=csvfilewithlabels")]),
    "EUROSTAT": dict(
        label="Eurostat bop_its6_det",
        browse=[("Eurostat Data Browser", "https://ec.europa.eu/eurostat/databrowser/view/bop_its6_det/default/table"
                 "?lang=en")],
        unduh=[("CSV mitra = Indonesia", "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/bop_its6_det/"
                "A.MIO_EUR.SD.CRE+DEB+BAL.ID.?format=SDMX-CSV&startPeriod=2010")]),
    "ABS": dict(
        label="ABS International Trade: Supplementary Information 2025",
        browse=[("Halaman rilis ABS", "https://www.abs.gov.au/statistics/economy/international-trade/"
                 "international-trade-supplementary-information-calendar-year/latest-release")],
        unduh=[("Tabel 7 (xlsx)", "https://www.abs.gov.au/statistics/economy/international-trade/"
                "international-trade-supplementary-information-calendar-year/2025/536805500407.xlsx"),
               ("Tabel 8 (xlsx)", "https://www.abs.gov.au/statistics/economy/international-trade/"
                "international-trade-supplementary-information-calendar-year/2025/536805500408.xlsx")]),
    "BATIS": dict(
        label="OECD-WTO Balanced Trade in Services (BaTIS)",
        browse=[("WTO Data Portal: BaTIS", "https://data.wto.org/en/dataset/batis")],
        unduh=[("CSV Indonesia × mitra", "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_BATIS@DF_BATIS,1.0/"
                "IDN..X+M.S.SD.A.USD_EXC.B?startPeriod=2019&format=csvfilewithlabels")]),
    "BATIS_METODE": dict(
        label="Dokumen metodologi BaTIS (OECD-WTO, Januari 2025)",
        browse=[("WTO: halaman dataset jasa", "https://www.wto.org/english/res_e/statis_e/trade_datasets_e.htm")],
        unduh=[("PDF metodologi", "https://www.wto.org/english/res_e/statis_e/daily_update_e/"
                "OECD-WTO_Batis_methodology_BPM6.pdf")]),
    "BI": dict(
        label="Bank Indonesia SEKI Tabel V.3",
        browse=[("Halaman SEKI Bank Indonesia", "https://www.bi.go.id/id/statistik/ekonomi-keuangan/seki/Default.aspx")],
        unduh=[("Tabel V.3 (xls)", "https://www.bi.go.id/SEKI/tabel/TABEL5_3.xls")]),
    "BI_PORT": dict(
        label="Bank Indonesia SEKI Tabel V.28 / V.29",
        browse=[("Halaman SEKI Bank Indonesia", "https://www.bi.go.id/id/statistik/ekonomi-keuangan/seki/Default.aspx")],
        unduh=[("Tabel V.29 (pdf)", "https://www.bi.go.id/SEKI/tabel/TABEL5_29.pdf")]),
    "BI_NPI": dict(
        label="Bank Indonesia: Laporan Neraca Pembayaran Indonesia",
        browse=[("Halaman laporan BI", "https://www.bi.go.id/id/publikasi/laporan/Default.aspx")],
        unduh=[("PDF NPI Triwulan I 2024", "https://www.bi.go.id/id/publikasi/laporan/Documents/NPI_Tw_I_2024.pdf")]),
    "Tourism Malaysia": dict(
        label="Tourism Malaysia: Malaysia's Tourist Profile 2024 (hal. 15)",
        browse=[("Portal statistik Tourism Malaysia", "https://data.tourism.gov.my/")],
        unduh=[("PDF Tourist Profile 2024 (±860 MB)",
                "https://data.tourism.gov.my/frontend/pdf/Malaysia_Tourist_Profile_2024%20v2.pdf")],
        catatan="File PDF sangat besar (±860 MB); angka ada di halaman 15."),
    "STB": dict(
        label="Singapore Tourism Board: rilis kinerja pariwisata 2024 (Jan–Sep 2024)",
        browse=[("Rilis STB 4 Feb 2025", "https://www.stb.gov.sg/about-stb/media-publications/media-centre/"
                 "singapore-achieves-historical-high-in-tourism-receipts-in-2024/")],
        unduh=[("PDF Annex A 2024", "https://isomer-user-content.by.gov.sg/1/7eff2b91-b8c6-4dac-a4c2-db5a19771868/"
                "YIR%202024_Annex%20A.pdf")]),
    "JTA": dict(
        label="Japan Tourism Agency: Survei Konsumsi Wisatawan Asing 2024",
        browse=[("Halaman survei JTA", "https://www.mlit.go.jp/kankocho/tokei_hakusyo/gaikokujinshohidoko.html")],
        unduh=[("PDF ringkasan 2024", "https://www.mlit.go.jp/kankocho/content/002020210.pdf")]),
    "MOTS": dict(
        label="Thailand Ministry of Tourism and Sports: penerimaan 2024",
        browse=[("Halaman kategori MOTS 2024", "https://www.mots.go.th/news/category/810")],
        unduh=[("Excel Q1–Q4 2024", "https://www.mots.go.th/images/v2022_c1331820-8936-4423-84cd-65278cebf658.xlsx")]),
    "Haji": dict(
        label="Haji: kuota dan BPIH (berita yang mengutip Kemenag/DPR)",
        browse=[("Kementerian Agama", "https://kemenag.go.id/")],
        unduh=[("Antara: BPIH 2024–2025", "https://www.antaranews.com/berita/4566750/"
                "dpr-pemerintah-setujui-bpih-2025-rp894-juta-jamaah-bayar-rp554-juta"),
               ("detik: kuota haji per tahun", "https://www.detik.com/sumut/berita/d-7965581/"
                "kuota-haji-indonesia-2026-batal-dipangkas-ini-rincian-kuota-dari-tahun-ke-tahun"),
               ("detik: biaya tiket haji", "https://news.detik.com/berita/d-8182587/"
                "ongkos-pesawat-haji-2026-rp-33-1-juta-komisi-viii-dpr-minta-turun-rp-1-juta")],
        catatan="Tidak ada file data resmi yang bisa diunduh; angka diambil dari berita. Dokumen DPR yang dulu "
                "ditautkan menolak akses (403), jadi dihapus."),
    "WB_KURS": dict(
        label="Bank Dunia: kurs resmi rata-rata tahunan (PA.NUS.FCRF)",
        browse=[("Halaman indikator Bank Dunia", "https://data.worldbank.org/indicator/PA.NUS.FCRF")],
        unduh=[("Excel semua negara", "https://api.worldbank.org/v2/en/indicator/PA.NUS.FCRF?downloadformat=excel")]),
    "WB_WDI": dict(
        label="Bank Dunia WDI: penerimaan pariwisata",
        browse=[("Halaman indikator Bank Dunia", "https://data.worldbank.org/indicator/ST.INT.RCPT.CD?locations=ID")],
        unduh=[("Excel semua negara", "https://api.worldbank.org/v2/en/indicator/ST.INT.RCPT.CD?downloadformat=excel")]),
    "ASEAN": dict(
        label="ASEANstats",
        browse=[("Portal data ASEANstats", "https://data.aseanstats.org/")], unduh=[],
        catatan="Halaman SITS lama meminta login; diganti halaman utama portal."),
    "IMF": dict(
        label="IMF Balance of Payments",
        browse=[("IMF Data", "https://data.imf.org/")],
        unduh=[("Struktur data BOP (API)", "https://api.imf.org/external/sdmx/2.1/dataflow/IMF.STA/BOP/latest"
                "?references=datastructure")]),
    "COMTRADE": dict(
        label="UN Comtrade (jasa, EBOPS 2010)",
        browse=[("UN Comtrade", "https://comtradeplus.un.org/")],
        unduh=[("JSON Indonesia 2022 (API pratinjau)", "https://comtradeapi.un.org/public/v1/preview/S/A/EB"
                "?reporterCode=360&period=2022")]),
    "TISMOS": dict(label="WTO TiSMoS", browse=[("WTO Data Portal: TiSMoS", "https://data.wto.org/en/dataset/tismos")],
                   unduh=[]),
    "UNCTAD": dict(label="UNCTADstat", browse=[("UNCTADstat Data Centre", "https://unctadstat.unctad.org/datacentre/")],
                   unduh=[]),
    "SUSENAS": dict(label="SUSENAS", browse=[("Katalog IHSN", "https://catalog.ihsn.org/catalog?sk=susenas")], unduh=[],
                    catatan="Link pencarian lama (404) diganti alamat katalog yang benar."),
    "SAKERNAS": dict(label="SAKERNAS", browse=[("Katalog IHSN", "https://catalog.ihsn.org/catalog?sk=sakernas")],
                     unduh=[], catatan="Link pencarian lama (404) diganti alamat katalog yang benar."),
    "PODES": dict(label="PODES", browse=[("Katalog IHSN", "https://catalog.ihsn.org/catalog?sk=podes")], unduh=[],
                  catatan="Link pencarian lama (404) diganti alamat katalog yang benar."),
    "BOK": dict(label="Bank of Korea", browse=[("Bank of Korea (English)", "https://www.bok.or.kr/eng/main/main.do")],
                unduh=[], catatan="ECOS (ecos.bok.or.kr) tidak bisa dibuka saat dicek; diganti halaman utama BOK."),
}

# source_inventory.csv source_id -> SRC key
INVENTORY = {"S01": "OECD_TIS", "S02": "EUROSTAT", "S03": "ABS", "S04": "BATIS", "S05": "BI",
             "S06": "BPS_KREDIT_PENGELUARAN", "S07": "BPS_KREDIT_KUNJUNGAN", "S08": "BPS_SWN",
             "S09": "Tourism Malaysia", "S10": "STB", "S11": "JTA", "S12": "MOTS", "S13": "Haji", "S14": "KEMENPAR",
             "S15": "ASEAN", "S16": "IMF", "S17": "WB_WDI", "S18": "COMTRADE", "S19": "TISMOS", "S20": "UNCTAD",
             "S21": "BI_PORT", "S22": "BI_NPI", "S23": "SUSENAS", "S24": "SAKERNAS", "S25": "PODES", "S26": "BPS_TSA",
             "S27": "BOK"}


def all_urls():
    return sorted({u for s in SRC.values() for _, u in s["browse"] + s["unduh"]})
