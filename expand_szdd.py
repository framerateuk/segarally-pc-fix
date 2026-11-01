#!/usr/bin/env python3
"""Expand Microsoft COMPRESS (SZDD) files in place, keeping their names.

  expand_szdd.py DIR [DIR ...]      every file whose first bytes are SZDD\x88\xf0\x27\x33

The Direct3D build reads MODELS\*.MD_/*.TE_ and SCROLL\SKY\*.BM_ through LZOpenFileA/LZRead, which
read an uncompressed file transparently (LZInit hands back the plain handle). docs/TECHNICAL.md.
"""
import os, struct, sys

MAGIC = b"SZDD\x88\xf0\x27\x33"

def expand(data):
    size = struct.unpack_from("<I", data, 10)[0]
    win = bytearray(b" " * 4096); pos = 4096 - 16
    out = bytearray(); i = 14
    while i < len(data) and len(out) < size:
        ctl = data[i]; i += 1
        for bit in range(8):
            if i >= len(data) or len(out) >= size: break
            if ctl & (1 << bit):
                b = data[i]; i += 1
                out.append(b); win[pos] = b; pos = (pos + 1) & 0xfff
            else:
                b1, b2 = data[i], data[i + 1]; i += 2
                off = b1 | ((b2 & 0xf0) << 4); ln = (b2 & 0x0f) + 3
                for k in range(ln):
                    b = win[(off + k) & 0xfff]
                    out.append(b); win[pos] = b; pos = (pos + 1) & 0xfff
    if len(out) != size: raise ValueError(f"expanded {len(out)} bytes, header says {size}")
    return bytes(out)

def expand_dirs(*tops):
    n = before = after = 0
    for top in tops:
        for root, _, files in os.walk(top):
            for f in files:
                p = os.path.join(root, f)
                with open(p, "rb") as fh: data = fh.read()
                if not data.startswith(MAGIC): continue
                out = expand(data)
                with open(p, "wb") as fh: fh.write(out)
                n += 1; before += len(data); after += len(out)
    print(f"  expanded {n} files: {before/1e6:.1f} MB -> {after/1e6:.1f} MB")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    expand_dirs(*sys.argv[1:])
