#!/usr/bin/env python3
"""Convert a raw binary into a $readmemh file: one 32-bit little-endian word per line."""

import sys

src, dst = sys.argv[1], sys.argv[2]
data = open(src, "rb").read()
data += b"\0" * (-len(data) % 4)
if not data:
    data = b"\0" * 4          # some tools reject an empty $readmemh file

with open(dst, "w") as f:
    for i in range(0, len(data), 4):
        f.write(f"{int.from_bytes(data[i:i + 4], 'little'):08x}\n")