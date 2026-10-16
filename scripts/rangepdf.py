"""Read selected pages of a huge remote PDF using HTTP Range requests (cached blocks, polite delay)."""
import io, sys, time, importlib.util
from pathlib import Path
_s = importlib.util.spec_from_file_location("s4", Path(__file__).resolve().parent / "s4_common.py")
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)

class RangeFile(io.RawIOBase):
    def __init__(self, url, block=2 << 20, cache_dir=None):
        self.url, self.block, self.pos, self.cache = url, block, 0, {}
        self.cache_dir = Path(cache_dir) if cache_dir else None
        r = C.get(url, headers={"Range": "bytes=0-0"}, stream=True)
        self.size = int(r.headers["Content-Range"].split("/")[1]); r.close()
        self.nreq = 0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, wh=0):
        self.pos = off if wh == 0 else self.pos + off if wh == 1 else self.size + off
        return self.pos
    def _blk(self, i):
        if i in self.cache: return self.cache[i]
        cp = self.cache_dir / f"blk_{i}.bin" if self.cache_dir else None
        if cp and cp.exists():
            b = cp.read_bytes()
        else:
            a = i * self.block; z = min(a + self.block, self.size) - 1
            r = C.get(self.url, headers={"Range": f"bytes={a}-{z}"})
            assert r.status_code == 206, r.status_code
            b = r.content; self.nreq += 1
            if cp: cp.parent.mkdir(parents=True, exist_ok=True); cp.write_bytes(b)
        self.cache[i] = b
        return b
    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        out = []; end = min(self.pos + n, self.size)
        while self.pos < end:
            i, o = divmod(self.pos, self.block)
            b = self._blk(i); take = b[o:o + end - self.pos]
            out.append(take); self.pos += len(take)
        return b"".join(out)
    def readinto(self, buf):
        d = self.read(len(buf)); buf[:len(d)] = d; return len(d)
