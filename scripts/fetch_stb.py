"""STB annexes (tourism performance charts) + release pages already saved by hand-run curl; Run: python -I scripts/fetch_stb.py"""
import importlib.util
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
RAW = C.RAW / "stb"
I = "https://isomer-user-content.by.gov.sg/1/"
FILES = {
 "annexA_JanSep2025.pdf": I + "7d282f34-2198-44a2-9525-4d174f67a005/Annex A.pdf",
 "YIR2024_annexA.pdf": I + "7eff2b91-b8c6-4dac-a4c2-db5a19771868/YIR 2024_Annex A.pdf",
 "YIR2023_annexA.pdf": I + "5f2863af-9103-40fc-9d51-144666e11cee/YIR_Annex A.pdf",
 "YIR2021_STB_Year_in_Review.pdf": I + "775e7ebd-8da4-4e19-a208-f0abec162e18/STB Year in Review 2021_Final 25 Jan_compressed.pdf",
}
for fn, u in FILES.items():
    st, p = C.save(u.replace(" ", "%20"), RAW, fn); print(fn, st, p.stat().st_size if p.exists() else 0)
# the HTML release pages (saved earlier with curl) -> register in manifest
REL = {
 "rel_jan_sep_2025.html": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/record-singapore-tourism-receipts-from-january-to-september-2025/",
 "rel_singapore-achieves-historical-high-in-tourism-receipts-in-20.html": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/singapore-achieves-historical-high-in-tourism-receipts-in-2024/",
 "rel_singapore-s-tourism-sector-posts-strong-recovery-in-2023--ex.html": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/singapore-s-tourism-sector-posts-strong-recovery-in-2023--exceeds-forecasts-for-tourism-receipts/",
 "rel_singapore-s-tourism-sector-recovers-strongly-in-2022--visito.html": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/singapore-s-tourism-sector-recovers-strongly-in-2022--visitor-numbers-expected-to-double-in-2023/",
 "rel_singapore-s-tourism-sector-remained-resilient-in-2021--ready.html": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/singapore-s-tourism-sector-remained-resilient-in-2021--ready-for-recovery-in-2022-and-beyond/",
 "rss_mediacentre.xml": "https://www.stb.gov.sg/about-stb/media-publications/media-centre/rss.xml",
}
for fn, u in REL.items():
    if (RAW / fn).exists(): C.add_manifest(RAW, fn, u, path=RAW / fn)
