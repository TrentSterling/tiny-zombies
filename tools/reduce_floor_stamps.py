#!/usr/bin/env python3
"""Apply the exact floor-radius-only adjustment to the compatibility build."""
import hashlib,sys
from pathlib import Path
src=Path(sys.argv[1]); dst=Path(sys.argv[2]); data=src.read_bytes()
assert src.resolve()!=dst.resolve(), 'Preserve the input'
assert hashlib.sha256(data).hexdigest()=='1be63cbf1a3887251b0b26067133e71068f7c820c96f5f1c28a9b8718c72f6df'
a=b'let radius=select(2,3,q.c.w<.5);';b=b'let radius=select(1,2,q.c.w<.5);'
assert data.count(a)==1
out=data.replace(a,b)
assert hashlib.sha256(out).hexdigest()=='c487bdb1aabeddb7c0ee6edcb2d059aabb2c32ea1be5cfa7a0c34717da3a4fc4'
assert not dst.exists() or dst.read_bytes()==out, 'Refuse to overwrite different output'
dst.write_bytes(out)
print(hashlib.sha256(out).hexdigest())
