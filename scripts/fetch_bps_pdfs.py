"""Download BPS publication PDFs via the PDF link returned by the WebAPI publication-detail endpoint.
Run after fetch_bps_api.py:  python -I scripts/fetch_bps_pdfs.py
PDF bytes are stored unchanged in 02_raw/bps/pdf; manifest rows use the URL with the key removed.
The download.php link is an opaque token (not the API key) but is still recorded as returned.
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bps_common as C

TARGETS = {
 # Statistik Wisatawan Nasional (outbound)
 "7344d8c9b1935d342f2ff9e7": "swn_2025", "8f41f59ea24192828f6c7275": "swn_2024",
 "a14ac9b0d02a074aac856dfb": "swn_2023", "1aaafdb1eca4c2bdda880782": "swn_2022",
 # Statistik Pengeluaran Wisman (spending), listed + earlier editions found by API search
 "5d0ec91c10b00f0302bc6757": "pengeluaran_wisman_2025", "7bd0bd596f54cf0f51b45030": "pengeluaran_wisman_2024",
 "b88772d443001a23da1acf41": "pengeluaran_wisman_2023", "72f620661a43c72cf15f10ad": "pengeluaran_wisman_2022",
 "5f780a406ed2d93e3aaac7a5": "pengeluaran_wisman_2021", "300a7a65c3ab81bfd6476e2d": "pengeluaran_wisman_2019",
 # Statistik Kunjungan Wisman (arrivals)
 "4fb8642851550952baead819": "kunjungan_wisman_2025", "a85d584df19ea65a5e2b3d0b": "kunjungan_wisman_2024",
 "0ba2b8f3f4f15dd18799f0c0": "kunjungan_wisman_2023", "4dcc6b622ae0c4e7ea6a61e8": "kunjungan_wisman_2022",
 "d79faad2c263388e94e160ee": "kunjungan_wisman_2021", "ddea1823bc9cd63789d51b05": "kunjungan_wisman_2020",
 "94ceb011540bd0cd73e3474c": "kunjungan_wisman_2019", "f2e676c8c2b7ae3346a28b88": "kunjungan_wisman_2018",
 "77480cacdb0a39aba3de84ce": "kunjungan_wisman_2017", "0873b4ec8f3645e62d8caa4c": "kunjungan_wisman_2016",
 # TSA
 "27b61f56c20226ca8ecfd974": "tsa_2023_2025",
}

for pid, stem in TARGETS.items():
    name = f"{stem}__{pid}.pdf"
    fp = os.path.join(C.RAW_PDF, name)
    if os.path.exists(fp) and "--refresh" not in sys.argv:
        print("cached", name); continue
    d = C.api_json(f"view/domain/0000/model/publication/lang/ind/id/{pid}/", f"pub_{pid}.json")
    dd = d.get("data", {})
    url = dd.get("pdf")
    if not url:
        print("NO PDF LINK", pid, dd.get("title")); continue
    if C.KEY in url:
        raise SystemExit("unexpected key in pdf url")
    r = C.http_get(url, stream=True)
    content = r.content
    if not content.startswith(b"%PDF"):
        print("NOT A PDF", name, content[:80]); continue
    C.save_raw(content, C.RAW_PDF, name, url)
    print("saved", name, len(content), flush=True)
