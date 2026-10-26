#!/usr/bin/env python3
"""
Apply KernelSU manual hooks for non-GKI kernels (4.19 Samsung trees).
Patches fs/exec.c, fs/open.c, fs/read_write.c, fs/stat.c.

Usage:
    python3 scripts/ksu_patch.py [kernel-source-root]

Default kernel root is the current directory.
"""

import sys
import re
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

EXTERN = "extern void {fn}({args});\n"

PATCHES = [
    {
        "file": "fs/exec.c",
        "fn": "ksu_handle_execveat",
        "proto": "ksu_handle_execveat(int *fd, struct filename **filename, void *argv, void *envp, int *flags)",
        "anchor_re": r"(return\s+__do_execve_file\()",
        "insert": "ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);\n\t",
        "extern_near": "static int __do_execve_file",
    },
    {
        "file": "fs/open.c",
        "fn": "ksu_handle_faccessat",
        "proto": "ksu_handle_faccessat(int *dfd, const char __user **filename, int *mode, int *flags)",
        "anchor_re": r"(if \(mode & ~S_IRWXO\))",
        "insert": "ksu_handle_faccessat(&dfd, &filename, &mode, NULL);\n\t",
        "extern_near": "SYSCALL_DEFINE3(faccessat",
    },
    {
        "file": "fs/read_write.c",
        "fn": "ksu_handle_vfs_read",
        "proto": "ksu_handle_vfs_read(struct file **file, char __user **buf, size_t *count, loff_t **pos)",
        "anchor_re": r"(ssize_t\s+ret;)",
        "insert": "ksu_handle_vfs_read(&file, &buf, &count, &pos);\n\t",
        "extern_near": "ssize_t vfs_read(",
    },
    {
        "file": "fs/stat.c",
        "fn": "ksu_handle_stat",
        "proto": "ksu_handle_stat(int *dfd, const char __user **filename, int *flags)",
        "anchor_re": r"(struct kstat stat;)",
        "insert": "ksu_handle_stat(&dfd, (const char __user **)&filename, &flags);\n\t",
        "extern_near": "int vfs_statx(",
    },
]


def patch_file(p: dict) -> bool:
    path = ROOT / p["file"]
    if not path.exists():
        print(f"[SKIP] {p['file']} not found")
        return False

    src = path.read_text()

    if p["fn"] in src:
        print(f"[OK]   {p['file']} already patched")
        return True

    # Insert extern prototype near anchor function
    extern_line = f"extern void {p['proto']};\n"
    near = p["extern_near"]
    if near not in src:
        print(f"[WARN] {p['file']}: anchor '{near}' not found, skipping extern")
    else:
        src = src.replace(near, extern_line + near, 1)

    # Insert hook call
    m = re.search(p["anchor_re"], src)
    if not m:
        print(f"[FAIL] {p['file']}: anchor regex not matched — patch manually")
        return False

    src = src[: m.start(1)] + p["insert"] + src[m.start(1) :]
    path.write_text(src)
    print(f"[DONE] {p['file']}")
    return True


ok = all(patch_file(p) for p in PATCHES)
sys.exit(0 if ok else 1)
