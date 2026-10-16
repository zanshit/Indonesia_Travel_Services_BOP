"""Save the news/official pages used for 03_extract/hajj_umrah.csv into 02_raw/hajj_umrah/ (HTML as retrieved) + manifest.
Run: python -I scripts/fetch_hajj_docs.py     (uses curl as a fallback because python-requests timed out on antaranews.com)"""
import importlib.util, subprocess
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
RAW = C.RAW / "hajj_umrah"
RAW.mkdir(parents=True, exist_ok=True)
D = "https://www.detik.com/"
A = "https://www.antaranews.com/berita/"
PAGES = {
    "antara_4565942_kemenag_usul_BPIH2025_89_67jt.html": A + "4565942/pemerintah-usulkan-kembali-bpih-tahun-2025-jadi-rp896-juta",
    "antara_4566750_panja_setujui_BPIH2025.html": A + "4566750/dpr-pemerintah-setujui-bpih-2025-rp894-juta-jamaah-bayar-rp554-juta",
    "antara_4569022_PUI_BPIH2025_vs_2024.html": A + "4569022/pui-apresiasi-penurunan-biaya-haji-2025",
    "detik_7776487_keppres6_2025_bipih_per_embarkasi.html": D + "hikmah/haji-dan-umrah/d-7776487/rincian-biaya-haji-2025-yang-dibayar-jemaah-per-embarkasi-menurut-keppres",
    "detik_7709401_menag_usul_BPIH2025_komponen.html": D + "hikmah/haji-dan-umrah/d-7709401/menag-usul-bpih-2025-rp-93-3-juta-jemaah-haji-bayar-rp-65-juta",
    "detik_8186135_BPIH_2017_2026_table.html": D + "hikmah/haji-dan-umrah/d-8186135/statistik-biaya-haji-10-tahun-terakhir-ada-penurunan-2-tahun-ini",
    "detik_3212553_BPIH2016.html": "https://news.detik.com/berita/d-3212553/menag-ongkos-haji-2016-turun-usd-132-tak-ada-penambahan-kuota",
    "detik_2926943_BPIH2015_perpres64.html": "https://news.detik.com/berita/d-2926943/biaya-haji-2015-turun-jokowi-semoga-meringankan-beban-jamaah",
    "detik_7965581_kuota_haji_2014_2025.html": D + "sumut/berita/d-7965581/kuota-haji-indonesia-2026-batal-dipangkas-ini-rincian-kuota-dari-tahun-ke-tahun",
    "detik_7707774_kuota_2024_241000.html": D + "hikmah/haji-dan-umrah/d-7707774/indonesia-dapat-kuota-haji-terbesar-sepanjang-sejarah-pada-2024",
    "antara_3606021_haji2023_realisasi_228093.html": A + "3606021/kuota-jamaah-haji-indonesia-tahun-ini-terserap-996-persen",
    "detik_8182587_bipih2026_komponen.html": "https://news.detik.com/berita/d-8182587/ongkos-pesawat-haji-2026-rp-33-1-juta-komisi-viii-dpr-minta-turun-rp-1-juta",
    "detik_8697173_BPIH2027_komponen.html": D + "hikmah/haji-dan-umrah/d-8697173/biaya-haji-dari-tahun-ke-tahun-jemaah-2027-bayar-rp-54-6-juta",
    "antara_5288806_keppres34_2025_BPIH2026.html": A + "5288806/presiden-resmi-tetapkan-biaya-haji-2026",
    "antara_5618112_BSI_siskopatuh2025_umrah_1_6jt.html": A + "5618112/bsi-perkuat-layanan-untuk-persiapan-operasional-cabang-di-arab-saudi",
    "detik_7994597_umrah_biaya_2025_KMA1021_2023.html": "https://news.detik.com/berita/d-7994597/info-biaya-umrah-2025-dan-cara-daftarnya-cek-di-sini",
    "detik_8603341_saudi_PEP_2025_umrah_18_03jt.html": D + "hikmah/haji-dan-umrah/d-8603341/rekor-jemaah-haji-umrah-tembus-19-5-juta-dalam-setahun",
    "detik_8185474_umrah_mandiri_vs_travel_KMA1021.html": D + "sulsel/berita/d-8185474/segini-perbandingan-perkiraan-biaya-umrah-mandiri-vs-travel",
}
for fn, u in PAGES.items():
    p = RAW / fn
    if p.exists():
        if fn not in C._man(RAW): C.add_manifest(RAW, fn, u, path=p)
        print("have", fn); continue
    st, _ = C.save(u, RAW, fn, timeout=40)
    if st != 200:
        r = subprocess.run(["curl", "-s", "-L", "-m", "60", "-H", "User-Agent: " + C.UA, "-o", str(p), "-w", "%{http_code}", u], capture_output=True)
        st = r.stdout.decode().strip()
        if st == "200": C.add_manifest(RAW, fn, u, path=p)
        else: p.unlink(missing_ok=True)
    print(st, fn, flush=True)
