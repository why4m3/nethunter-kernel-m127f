#!/usr/bin/env python3
"""
Pack a boot.img into an Odin-flashable AP_*.tar.md5.

Usage:
    python3 scripts/build_odin_tar.py <boot.img> [output.tar.md5]

Output defaults to AP_nethunter_m127f.tar.md5 in the current directory.
The appended md5 checksum is what Odin validates — a missing or wrong md5
causes Odin to reject the file silently.
"""

import sys
import hashlib
import tarfile
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: build_odin_tar.py <boot.img> [output.tar.md5]")

boot = Path(sys.argv[1])
if not boot.exists():
    sys.exit(f"error: {boot} not found")

out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("AP_nethunter_m127f.tar.md5")

# Build tar (ustar format, no compression — Odin requires this)
tar_path = out.with_suffix("")  # temporary .tar before appending md5
with tarfile.open(tar_path, "w:", format=tarfile.USTAR_FORMAT) as tf:
    tf.add(boot, arcname="boot.img")

# Compute md5 of the tar
data = tar_path.read_bytes()
digest = hashlib.md5(data).hexdigest()

# Append md5 + newline and rename to .tar.md5
with open(out, "wb") as f:
    f.write(data)
    f.write(f"{digest}  {out.name}\n".encode())

tar_path.unlink()

size_mb = out.stat().st_size / 1024 / 1024
print(f"Created: {out}  ({size_mb:.1f} MB)")
print(f"MD5:     {digest}")
print("Flash via Odin → AP slot. BL/CP/CSC empty. Re-Partition OFF.")
