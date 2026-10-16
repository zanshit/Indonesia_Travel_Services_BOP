"""Shared helpers for the SDMX fetch scripts (polite HTTP, manifest, tidy schema, anchors).
Loaded by the fetch_*.py scripts via importlib so that they can be run with `python -I`."""
import csv
import hashlib
import io
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "02_raw"
EXTRACT = ROOT / "03_extract"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
SLEEP = 1.5          # seconds between requests (>= 1 s required)
MAX_TRIES = 5
TIDY_COLS = ["source", "line", "reporter", "partner_iso3", "partner_name", "flow_idn", "item",
             "item_label", "year", "quarter", "value", "currency", "unit_mult", "adjustment",
             "methodology_type", "obs_status", "url", "retrieved_at"]
MANIFEST_COLS = ["file", "url", "retrieved_at_utc", "sha256", "http_status", "rows"]

_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept": "*/*"})


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_manifest(raw_dir):
    p = raw_dir / "manifest.csv"
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8") as f:
        return {r["file"]: r for r in csv.DictReader(f)}


def save_manifest(raw_dir, man):
    with open(raw_dir / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS)
        w.writeheader()
        for k in sorted(man):
            w.writerow(man[k])


def count_csv_rows(body):
    try:
        text = body.decode("utf-8-sig")
        if not text.lstrip().startswith(("STRUCTURE", "DATAFLOW", "dataflow")) and "," not in text.split("\n", 1)[0]:
            return 0
        return max(sum(1 for _ in csv.reader(io.StringIO(text))) - 1, 0)
    except Exception:
        return 0


def get_with_retry(url):
    """GET with exponential backoff on 429/5xx/network errors. Returns Response (any final status)."""
    delay = 4
    last = None
    for attempt in range(1, MAX_TRIES + 1):
        try:
            r = _session.get(url, timeout=300)
            last = r
            if r.status_code == 429 or r.status_code >= 500:
                wait = delay
                ra = r.headers.get("Retry-After")
                if ra and ra.isdigit():
                    wait = max(wait, int(ra))
                print(f"  HTTP {r.status_code}; retry {attempt}/{MAX_TRIES} in {wait}s", flush=True)
                time.sleep(wait)
                delay *= 2
                continue
            return r
        except requests.RequestException as e:
            print(f"  network error {type(e).__name__}; retry {attempt}/{MAX_TRIES} in {delay}s", flush=True)
            time.sleep(delay)
            delay *= 2
    if last is not None:
        return last
    raise RuntimeError(f"giving up on {url}")


def fetch(url, raw_dir, filename, is_csv=True, refresh=False):
    """Fetch url -> raw_dir/filename (bytes unchanged) and upsert manifest. Idempotent: skips if file and
    manifest entry (same url) already exist, unless refresh. Non-200 bodies (e.g. 404 NoResultsFound,
    400 invalid query) are stored as <filename>.http<status>.txt and recorded with rows=0.
    Returns (http_status, path_of_saved_file or None)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    man = load_manifest(raw_dir)
    # already have it?
    for fn, row in man.items():
        if row["url"] == url and (raw_dir / fn).exists() and not refresh:
            print(f"  cached: {fn}", flush=True)
            return int(row["http_status"]), (raw_dir / fn)
    print(f"GET {url}", flush=True)
    r = get_with_retry(url)
    time.sleep(SLEEP)
    body = r.content
    fn = filename if r.status_code == 200 else f"{filename}.http{r.status_code}.txt"
    (raw_dir / fn).write_bytes(body)
    rows = count_csv_rows(body) if (is_csv and r.status_code == 200) else (0 if r.status_code != 200 else "")
    man[fn] = {"file": fn, "url": url, "retrieved_at_utc": now_utc(),
               "sha256": hashlib.sha256(body).hexdigest(), "http_status": r.status_code, "rows": rows}
    save_manifest(raw_dir, man)
    print(f"  -> {fn}: HTTP {r.status_code}, {len(body)} bytes, rows={rows}", flush=True)
    return r.status_code, (raw_dir / fn)


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def man_lookup(raw_dir, path):
    return load_manifest(raw_dir)[Path(path).name]


def neg(s):
    """Negate a numeric string exactly (Decimal); '' stays ''."""
    if s is None or s == "":
        return ""
    try:
        d = -Decimal(s)
    except InvalidOperation:
        return ""
    if d == 0:
        d = Decimal(0)
    return format(d, "f")


def split_period(tp):
    """'2023' -> ('2023',''); '2023-Q2' -> ('2023','Q2'); '2023-06' -> ('2023','M06')."""
    tp = tp.strip()
    if "-Q" in tp:
        y, q = tp.split("-Q")
        return y, "Q" + q
    if len(tp) == 7 and tp[4] == "-":
        return tp[:4], "M" + tp[5:]
    return tp, ""


def write_tidy(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TIDY_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in TIDY_COLS})


def check_anchors(tidy_rows, anchors, out_path):
    """anchors: list of dict(name, expected(str), filt: dict of column->value). Expect exactly one match.
    Tolerance = half a unit in the last decimal place of the expected string."""
    results = []
    for a in anchors:
        m = [r for r in tidy_rows if all(r.get(k) == v for k, v in a["filt"].items())]
        exp = Decimal(a["expected"])
        dp = -exp.as_tuple().exponent
        tol = Decimal("0.5") * (Decimal(10) ** -dp)
        if len(m) != 1:
            status, got = "FAIL", f"{len(m)} matching rows"
        else:
            got = m[0]["value"]
            try:
                status = "PASS" if abs(Decimal(got) - exp) <= tol else "FAIL"
            except InvalidOperation:
                status = "FAIL"
        results.append({"anchor": a["name"], "expected": a["expected"], "got": got, "status": status})
        print(f"  ANCHOR {status}: {a['name']} expected {a['expected']} got {got}", flush=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["anchor", "expected", "got", "status"])
        w.writeheader()
        w.writerows(results)
    return results
