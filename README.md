# Kali NetHunter Kernel — Samsung Galaxy M12 (SM-M127F)

Custom **Kali NetHunter–capable kernel** for the Samsung Galaxy M12 (**SM-M127F**, Exynos 850 / `universal3830`, Android 13 / One UI Core 5.1, kernel **4.19.111**).

To my knowledge this is the **first NetHunter kernel for the M127F** — the device is not on the official NetHunter device list. Built from source, validated on real hardware (monitor mode + USB Wi‑Fi adapter confirmed working).

> ⚠️ **For authorized security testing and education only.** You are responsible for complying with the law in your jurisdiction.

---

## Features

| Capability | Status |
|---|---|
| **rtl8188eus** Wi‑Fi driver (built‑in) — monitor mode + packet injection | ✅ |
| Realtek RTL8188EUS adapter (e.g. TP‑Link TL‑WN722N v2) over USB‑OTG | ✅ confirmed (`wlan1`, `type monitor`) |
| **KernelSU** root (kernel‑level, via [rsuntk](https://github.com/rsuntk/KernelSU) fork) | ✅ |
| Samsung **DEFEX** LSM disabled (root/chroot friendly) | ✅ |
| **USB HID gadget** — BadUSB / DuckHunter HID attacks | ✅ (`CONFIG_USB_CONFIGFS_F_HID=y`) |
| **USB RNDIS gadget** — USB MITM (Windows targets) | ✅ (`CONFIG_USB_CONFIGFS_RNDIS=y`) |
| USB‑OTG host (DWC3 dual‑role, like stock) | ✅ |
| CFG80211 / WEXT (airmon‑ng) + `CONFIG_PACKET` (raw sockets) | ✅ |

> USB MITM over **ECM (Linux/Mac targets)** is not enabled in this build — RNDIS covers Windows. Trivial one‑line config add if needed.

---

## Why this exists / notes

- Base kernel: **[spacingbat3/android_kernel_samsung-m127f_a13](https://github.com/SpacingBat3/android_kernel_samsung-m127f_a13)** (the only proper M127F source). Defconfig: `exynos850-m12nsxx-spacingbat3_defconfig`.
- **Toolchain matters.** This 4.19 Samsung tree must be built with the maintainer's toolchain — **AOSP Clang `r353983c` (build 5484270, clang 9.0.3) + GCC 4.9 binutils**. Building with a modern Clang (e.g. 21) compiles but produces a **non‑booting kernel** (boot‑loop). See [`docs/BUILD.md`](docs/BUILD.md).
- **Root: KernelSU, not Magisk.** Official Magisk boot‑loops on Exynos 850 / M12 / A13 (a documented issue). KernelSU integrated into the kernel sidesteps it entirely.
- **AVB / vbmeta:** flashing a modified boot trips Samsung AVB. A *stock* vbmeta with only the verity‑disable flag flipped passes Samsung anti‑rollback (a from‑scratch vbmeta does not). See [`flash/FLASH_GUIDE.md`](flash/FLASH_GUIDE.md).

---

## Quick start (prebuilt)

Prebuilt `boot.img` is provided for firmware **M127FXXS9DXJ1 (SER)**. Other firmware: rebuild or repack with your own stock `boot.img` (see flash guide).

1. Unlock bootloader (OEM unlock), confirm `OEM LOCK: OFF(U)` in Download Mode.
2. Flash via **Odin** (AP slot): the provided `AP_*.tar.md5`.
3. Boot, install the **KernelSU manager** APK ([rsuntk releases](https://github.com/rsuntk/KernelSU/releases)), grant root.
4. Plug a RTL8188EUS adapter via USB‑C OTG → `wlan1` appears.

```sh
# in a root shell (KernelSU)
iw dev wlan1 set type monitor
ip link set wlan1 up
iw dev wlan1 info          # -> type monitor
```

Full flashing + recovery instructions: [`flash/FLASH_GUIDE.md`](flash/FLASH_GUIDE.md).

---

## Build from source

See [`docs/BUILD.md`](docs/BUILD.md) — toolchain, exact `make` command, rtl8188eus + KernelSU integration steps, and the manual KernelSU hooks for 4.19.

---

## Credits

- **[SpacingBat3](https://github.com/SpacingBat3/android_kernel_samsung-m127f_a13)** — M127F kernel source & defconfig.
- **[aircrack-ng/rtl8188eus](https://github.com/aircrack-ng/rtl8188eus)** — Wi‑Fi driver with monitor/injection.
- **[rsuntk/KernelSU](https://github.com/rsuntk/KernelSU)** — KernelSU fork for non‑GKI / legacy Samsung kernels.
- **[Kali NetHunter](https://www.kali.org/get-kali/#kali-mobile)** — the platform this kernel targets.

## License

GPLv2 (inherited from the Linux kernel). Kernel source modifications are published in compliance with GPLv2.
