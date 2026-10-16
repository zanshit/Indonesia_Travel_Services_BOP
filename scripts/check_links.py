"""Open every link in scripts/sources.py and write 04_qa/link_check.csv (read by build_excel.py).

Plain HTTP GET with a browser user agent first; anything that is not a clean 200 is retried in headless Chromium
(Playwright). bps.go.id pages answer bots with a Cloudflare check ('Just a moment...'); those are recorded as
'anti-bot' rather than broken.

Run:  python -I scripts/check_links.py      (needs: pip install playwright; a Chromium/headless_shell binary)
Set CHROMIUM=/path/to/headless_shell to override the browser binary.
"""
import csv
import datetime as dt
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import all_urls  # noqa: E402
import urllib.request
import ssl

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0.0.0 Safari/537.36")
CA = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").exists() else None)
ctx = ssl.create_default_context(cafile=CA)


def plain(u):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en,id;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
            body = r.read(65536)
            return r.status, r.headers.get("Content-Type", ""), r.geturl(), body
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), u, b""
    except Exception as e:  # noqa: BLE001
        return 0, type(e).__name__ + ": " + str(e)[:120], u, b""


def browser(page, u):
    downloads = []
    page.on("download", lambda d: downloads.append(d))
    try:
        resp = page.goto(u, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)  # let JS challenges (Cloudflare etc.) finish
        title = page.title()[:90]
        body = page.inner_text("body")[:300].replace("\n", " ") if not downloads else ""
        return (resp.status if resp else 0), "html", page.url, f"{title} || {body[:160]}"
    except Exception as e:  # noqa: BLE001
        if downloads or "Download is starting" in str(e):
            fn = downloads[0].suggested_filename if downloads else "(download)"
            return 200, "download", u, fn
        return 0, "error", u, str(e).splitlines()[0][:140]


def verdict(st, kind, title):
    if st == 200 and "Not Authorized" not in title and "404" not in title[:10]:
        return "OK"
    if re.search(r"Just a moment|Tunggu sebentar", title):
        return "OK di browser (anti-bot, tidak bisa diuji otomatis)"
    return f"GAGAL ({st or kind})"


def main():
    urls = all_urls()
    rows = []
    today = dt.date.today().isoformat()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"),
                              args=["--ignore-certificate-errors"])
        c = b.new_context(user_agent=UA, accept_downloads=True, ignore_https_errors=True)
        for u in urls:
            st, ct, fin, body = plain(u)
            kind = "html" if "html" in ct.lower() else ct
            title = ""
            if st == 200 and "html" in ct.lower():
                m = re.search(rb"<title[^>]*>(.*?)</title>", body, re.S | re.I)
                title = m.group(1).decode("utf-8", "replace").strip()[:90] if m else ""
            how = "plain"
            if st != 200 or ("html" in ct.lower() and not title):
                page = c.new_page()
                st, kind, fin, title = browser(page, u)
                page.close()
                how = "chromium"
            v = verdict(st, kind, title)
            print(v, st, how, kind[:30], "|", title[:60], "|", u[:100], flush=True)
            rows.append([u, st, v, how, kind, title, today])
        b.close()
    out = Path(__file__).resolve().parents[1] / "04_qa" / "link_check.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["url", "http_status", "verdict", "checked_with", "content", "title", "checked_on"]]
                                + rows)
    print("saved", out)


if __name__ == "__main__":
    main()
