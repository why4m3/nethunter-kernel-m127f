# Building the M127F NetHunter kernel

## TL;DR — the one thing that matters

This Samsung 4.19 tree **must** be built with the maintainer's toolchain:
**AOSP Clang `r353983c` (build 5484270, clang 9.0.3) + GCC 4.9 binutils.**
A modern Clang (e.g. 21) *compiles* but produces a **non-booting kernel** (boot-loop). Don't.

## Toolchain

googlesource is often unreachable from some regions — use GitHub mirrors:

```sh
mkdir -p toolchains && cd toolchains
git clone --depth 1 https://github.com/crdroidandroid/android_prebuilts_clang_host_linux-x86_clang-5484270 clang-5484270
git clone --depth 1 https://github.com/LineageOS/android_prebuilts_gcc_linux-x86_aarch64_aarch64-linux-android-4.9 aarch64-linux-android-4.9
cd ..
```

## Config

Start from the maintainer defconfig and apply exactly these:

```sh
export PLATFORM_VERSION=13 ANDROID_MAJOR_VERSION=t ARCH=arm64
export KCFLAGS="-mtune=cortex-a55" KCPPFLAGS="-mtune=cortex-a55"
MK="make O=out ARCH=arm64 \
  CROSS_COMPILE=$PWD/toolchains/aarch64-linux-android-4.9/bin/aarch64-linux-android- \
  CLANG_PATH=$PWD/toolchains/clang-5484270/bin/ \
  CLANG_TRIPLE=aarch64-linux-gnu-"

$MK exynos850-m12nsxx-spacingbat3_defconfig
./scripts/config --file out/.config \
    -e RTL8188EU \          # Wi-Fi driver (monitor + injection)
    -d MAC80211 \           # off — device uses SCSC full-MAC; mac80211 unused
    -d SECURITY_DEFEX \     # Samsung anti-root LSM off
    -e KSU                  # KernelSU
$MK olddefconfig
```

Kept at maintainer defaults (do **not** change — needed to boot): `FORTIFY_SOURCE=y`,
`LOCALVERSION="-spacingbat3_v4"`, `LOCALVERSION_AUTO=y`. (vermagic does **not** need to
match stock vendor modules — the maintainer kernel boots with a non-matching vermagic.)

## Driver — aircrack-ng/rtl8188eus (built-in)

```sh
git clone https://github.com/aircrack-ng/rtl8188eus drivers/net/wireless/rtl8188eus
# wire into the tree:
#   drivers/net/wireless/Kconfig : add  source "drivers/net/wireless/rtl8188eus/Kconfig"  before  endif # WLAN
#   drivers/net/wireless/Makefile: add  obj-$(CONFIG_RTL8188EU) += rtl8188eus/
#   driver Makefile (clang 9 compat): add near the top
#     EXTRA_CFLAGS += -Wno-unknown-warning-option
#     EXTRA_CFLAGS += -Wno-error
```

## Root — KernelSU (rsuntk fork, manual hooks)

Official KernelSU dropped non-GKI; use the rsuntk fork (no kprobe — manual hooks):

```sh
git clone https://github.com/rsuntk/KernelSU
ln -sf ../KernelSU/kernel drivers/kernelsu
printf '\nobj-$(CONFIG_KSU) += kernelsu/\n' >> drivers/Makefile
sed -i '/^endmenu/i source "drivers/kernelsu/Kconfig"' drivers/Kconfig
```

Root grant (`task_fix_setuid` LSM) and manager comms (fd+ioctl) self-register.
Manually add 3 sucompat/ksud hooks — **place the call AFTER the local declarations**
(C90 `-Werror=declaration-after-statement`):

- `fs/exec.c` → in `do_execveat_common`, before `return __do_execve_file(...)`:
  `ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);`
- `fs/open.c` → in `do_faccessat`, after the declarations:
  `ksu_handle_faccessat(&dfd, &filename, &mode, NULL);`
- `fs/read_write.c` → in `vfs_read`, after `ssize_t ret;`:
  `ksu_handle_vfs_read(&file, &buf, &count, &pos);`
- `fs/stat.c` → in `vfs_statx`, after the local declarations:
  `ksu_handle_stat(&dfd, (const char __user **)&filename, &flags);`
  (covers `stat`/`lstat`/`newfstatat`/`statx` — `vfs_fstatat` is an inline
  wrapper around `vfs_statx`). Needed so `ls`/`test -f` existence checks on
  `/system/bin/su` succeed — NetHunter probes su existence before exec.

(Each needs an `extern` prototype above the function — see `scripts/ksu_patch.py`.)

### Make su work in app terminals (seccomp)

Android's zygote launches every app under a seccomp filter, and upstream
`__is_su_allowed()` in `KernelSU/kernel/feature/sucompat.c` bails out early when
`TIF_SECCOMP` is set — which disables `su` in **every** app shell (Termux,
NetHunter). Remove that early-return so sucompat applies to allowed uids
regardless of seccomp:

```c
/* delete these two lines in __is_su_allowed(): */
if (likely(test_thread_flag(TIF_SECCOMP)))
    return false;
```

## Build

```sh
$MK -j"$(nproc)"
# -> out/arch/arm64/boot/Image
```

Sanity:
```sh
strings out/arch/arm64/boot/Image | grep '^4\.19\.'        # 4.19.111-spacingbat3_v4-...
grep -c 'ksu_\|rtl8188' out/System.map                     # KernelSU + driver present
```

## Package for Odin

magiskboot repack (keep stock ramdisk + dtb, swap only the kernel) → see
`flash/FLASH_GUIDE.md`. Build the Odin `.tar.md5` with a validated md5
(`scripts/build_odin_tar.py`) — a malformed md5 makes Odin reject it.
