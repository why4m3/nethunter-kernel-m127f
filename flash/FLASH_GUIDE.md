# Flashing — Samsung Galaxy M12 (SM-M127F)

> No TWRP exists for this device — everything is done via **Odin** (Download Mode).
> Test on a device you can afford to recover. Keep the **full stock firmware** for your
> exact build downloaded *before* you start — it is your only way back.

## Prerequisites

- Bootloader unlocked: in Download Mode the screen must show **`OEM LOCK: OFF(U)`**
  and **`KG/RMM STATE`** not `Prenormal`.
- Anti-rollback: only flash binaries with SW REV ≥ your fuse (shown as `AP SWREV S:n`).
  Build `boot.img` from a stock `boot.img` of the **same firmware** that is on the phone.
- Odin (Windows) + Samsung USB drivers. Use a **USB 2.0** port (3.0 can hang on
  `SetupConnection`).

## 1. Build the flashable

Take the stock `boot.img` for your firmware, swap in the built `Image`
(keep the stock ramdisk + dtb), and make an Odin tar:

```sh
magiskboot unpack stock_boot.img        # gives kernel/ramdisk/dtb
cp Image kernel                          # raw Image, NOT Image.gz
magiskboot repack stock_boot.img out_boot.img
tar -H ustar -cf boot.tar boot.img      # boot.img = out_boot.img
# append md5 (validate it — see scripts/build_odin_tar.py), rename to boot.tar.md5
```

## 2. AVB / vbmeta (Samsung)

A modified boot fails Samsung Verified Boot. A **from-scratch** disabled vbmeta is
rejected by anti-rollback (`SB REV CHECK FAIL(VBMETA) DEVICE:0x9 BINARY:0x0`).
Instead, take the **stock** `vbmeta.img` and flip only the AVB flags byte to `0x03`
(verity + verification disabled) — keeps Samsung's version metadata so anti-rollback
passes. AVB is big-endian: the `flags` u32 is at header offset 120, so `0x03` lands in
byte **123**; `cmp -l stock patched` must show exactly one changed byte. `avbtool
info_image` should then read `Flags: 3`.

Flash `boot.img` + patched `vbmeta.img` together in one Odin **AP** tar.

## 3. Flash (Odin)

1. Phone → Download Mode (Vol Down + Power to off, then Vol Up + Vol Down + USB → Vol Up).
2. Odin (as admin) → wait for `0:[COMx] Added!!`.
3. **AP** = your `AP_*.tar.md5`. BL/CP/CSC empty. Options: Re-Partition **off**, Auto Reboot on.
4. Start → PASS → reboot. If it drops to recovery, **Wipe data/factory reset** → reboot.
5. First boot after a kernel change can take several minutes — don't pull the cable.

## 4. Root (KernelSU)

- Install the **KernelSU manager** APK for the matching version
  (https://github.com/rsuntk/KernelSU/releases — download it **on the phone**).
- Open it → should read **Working**. Grant root to your terminal app under **Superuser**.
- If `su` says *not found* right after granting, **reboot once** (the ksud daemon
  finishes setup on the next boot).

## 5. Use the adapter

Plug a RTL8188EUS adapter (e.g. TL-WN722N v2) via a USB-C OTG adapter:

```sh
ls -l /sys/class/net/wlan1/device/driver   # -> .../8188eu
iw dev wlan1 set type monitor
ip link set wlan1 up
iw dev wlan1 info                           # type monitor
```

Then install Kali NetHunter (chroot) for `airmon-ng` / `aireplay-ng` / `wifite`.

## Recovery (if it won't boot)

Odin → flash the **full stock firmware** (BL + AP + CP + CSC) of your build. This is
why you keep it downloaded. Only data on the boot partition is touched by these steps;
a stock reflash + factory reset always brings the phone back.
