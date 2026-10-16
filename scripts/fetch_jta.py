"""Japan Tourism Agency inbound consumption survey (訪日外国人消費動向調査 / インバウンド消費動向調査): calendar-year tables.
Run: python -I scripts/fetch_jta.py -> 02_raw/jta/"""
import importlib.util
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
RAW = C.RAW / "jta"
B = "https://www.mlit.go.jp/kankocho/content/"
PAGE = "https://www.mlit.go.jp/kankocho/tokei_hakusyo/gaikokujinshohidoko.html"
FILES = {  # file -> description
 "002025515.xls": "2025 calendar year tables (preliminary/2nd prelim)", "002022649.xls": "2024 calendar-year tables",
 "002020300.xls": "2023 calendar-year tables", "002021087.xls": "2022 calendar-year tables (trial values; all-nationality only?)",
 "002020401.xls": "2019 calendar-year tables", "002026221.xls": "2020 Q1 tables (only quarter surveyed)",
 "002020394.xls": "2021 Q4 tables", "002020390.pdf": "2021 annual trial estimate summary",
 "002020010.pdf": "2025 report", "002020012.pdf": "2024 report", "002020046.pdf": "2025 calendar-year summary (survey overview)",
 "002026218.pdf": "2020 annual trial estimate summary",
 "002020210.pdf": "2024 calendar-year summary", "002020295.pdf": "2023 calendar-year summary",
 "002020310.pdf": "2022 calendar-year summary (trial values)", "002020396.pdf": "2019 calendar-year summary (definitive)",
 "002020023.pdf": "2019 report",
}
for fn in FILES:
    st, p = C.save(B + fn, RAW, fn); print(fn, st, p.stat().st_size if p.exists() else 0, FILES[fn], flush=True)
if (RAW / "gaikokujinshohidoko.html").exists():
    C.add_manifest(RAW, "gaikokujinshohidoko.html", PAGE, path=RAW / "gaikokujinshohidoko.html")
