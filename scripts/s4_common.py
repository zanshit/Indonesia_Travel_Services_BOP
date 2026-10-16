"""Shared helpers for session-4 scripts (Kemenpar, destination side, hajj/umrah).
Polite HTTP (>=1.5 s), browser UA, manifest.csv in the (columns: file,url,retrieved_at_utc,sha256,bytes)."""
import csv, hashlib, time
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "02_raw"
EXTRACT = ROOT / "03_extract"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
SLEEP = 1.5
MCOLS = ["file", "url", "retrieved_at_utc", "sha256", "bytes"]
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9,id;q=0.8"})
_last = [0.0]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url, retries=3, stream=False, **kw):
    for a in range(retries):
        w = SLEEP - (time.time() - _last[0])
        if w > 0:
            time.sleep(w)
        try:
            r = S.get(url, timeout=kw.pop("timeout", 120), stream=stream, **kw)
            _last[0] = time.time()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(5 * (a + 1)); continue
            return r
        except requests.RequestException as e:
            _last[0] = time.time()
            print("  net err", type(e).__name__, url[:90]); time.sleep(5 * (a + 1))
    return None


def _man(d):
    p = d / "manifest.csv"
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8") as f:
        return {r["file"]: r for r in csv.DictReader(f)}


def add_manifest(d, fname, url, data=None, path=None):
    """Append/replace a manifest row. Only touches rows for files this script wrote."""
    d = Path(d)
    if path is not None:
        h = hashlib.sha256(); n = 0
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b); n += len(b)
        sha, size = h.hexdigest(), n
    else:
        sha, size = hashlib.sha256(data).hexdigest(), len(data)
    m = _man(d)
    m[fname] = dict(file=fname, url=url, retrieved_at_utc=now(), sha256=sha, bytes=size)
    with open(d / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MCOLS, extrasaction="ignore"); w.writeheader()
        for k in sorted(m):
            w.writerow(m[k])


def save(url, d, fname, refresh=False, **kw):
    """Download url into d/fname (binary) and register in manifest. Returns (status, path)."""
    d = Path(d); d.mkdir(parents=True, exist_ok=True)
    p = d / fname
    if p.exists() and not refresh:
        if fname not in _man(d):
            add_manifest(d, fname, url, path=p)
        return 200, p
    r = get(url, **kw)
    if r is None:
        return 0, p
    if r.status_code != 200:
        return r.status_code, p
    p.write_bytes(r.content)
    add_manifest(d, fname, url, data=r.content)
    return 200, p
