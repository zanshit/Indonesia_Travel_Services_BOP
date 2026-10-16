"""BPS WebAPI var 178 'Jumlah Jemaah Haji yang Diberangkatkan ke Tanah Suci Mekah Menurut Provinsi' -> 02_raw/hajj_umrah/.
Key from env BPS_API_KEY, never saved (stored URLs show KEY). Run: python -I scripts/fetch_hajj_bps.py"""
import importlib.util, os, sys, json
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)
KEY = os.environ.get("BPS_API_KEY") or sys.exit("BPS_API_KEY not set")
RAW = C.RAW / "hajj_umrah"; RAW.mkdir(parents=True, exist_ok=True)
H = "https://webapi.bps.go.id/v1/api/"
def call(path, fname):
    r = C.get(H + path + f"/key/{KEY}/")
    if r is None or r.status_code != 200:
        print(fname, "HTTP", None if r is None else r.status_code); return None
    body = r.content.replace(KEY.encode(), b"KEY")
    (RAW / fname).write_bytes(body)
    C.add_manifest(RAW, fname, H + path + "/key/KEY/", data=body)
    return r.json()
j = call("list/model/th/domain/0000/var/178", "bps_var178_years.json")
yrs = j["data"][1] if j else []
print(json.dumps(yrs, ensure_ascii=False)[:600])
ths = sorted(y["th_id"] for y in yrs)
print("th ids available:", ths)
for k in range(0, len(ths), 3):   # API allows max 3 years per call
    chunk = ths[k:k + 3]
    d = call("list/model/data/domain/0000/var/178/th/" + ";".join(str(t) for t in chunk), f"bps_var178_data_th{chunk[0]}-{chunk[-1]}.json")
    print(chunk, d.get("status") if d else None)
