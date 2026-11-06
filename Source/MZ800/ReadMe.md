# SHARP MZ-800

RomWBW runs on the SHARP MZ-800 with a 512K MemExt memory expansion
(PEHU or Luftner board, detected at startup). The image is ROM-less:
a loader puts it into MemExt RAM and starts HBIOS.

## Unicard loader (`mz800-ldr.mzf`)

1. Copy `Binary/mz800-ldr.mzf` and `Binary/MZ800_std.rom` to the Unicard
   SD card, into the same directory or the image into `/romwbw/`.
2. Start `mz800-ldr.mzf` from the Unicard Manager, or name it in
   `/unicard/mzfloader.cfg` to start it at power on.

The loader detects MemExt (without it, it stops with a message),
moves itself into the common bank, reads the image sequentially
(Unicard firmware 0.26 has no working SEEK) into banks $80.. and jumps
to HBIOS. The full `.rom` image also fills the RAM disk with the RomWBW
utilities; the `.upd` image (first 128K) leaves it empty.

## Floppy boot (`mz800-ipl.bin`, `MZSYS.COM`)

A floppy in one of the formats of Lamac's CP/M for the MZ-800 (720K,
360K, HD 1.44M or 1.2M with the HD modification) in the MZ layout
(cylinder 0, side 1 is the IPL boot track of 16 sectors of 256 bytes,
double density) boots RomWBW from drive 0 at power on:

- the boot track holds `mz800-ipl.bin`: the IPLPRO header and a loader
  that detects MemExt, reads the CP/M directory of the disk and loads
  the file `ROMWBW.ROM` (user 0) into banks $80.. like the Unicard
  loader, then starts HBIOS;
- `ROMWBW.ROM` is `MZ800_std.rom` (fills the RAM disk too) or
  `MZ800_std.upd` (loads three times quicker, empty RAM disk);
- optionally a CP/M system in the reserved tracks (`SYSCOPY`) lets the
  boot loader boot the floppy itself (disk unit of FD0), A: is then the
  floppy.

On a RomWBW system, a disk formatted by Lamac's CP/M is made bootable
with:

    MZSYS C:
    PIP C:ROMWBW.ROM=...MZ800_STD.ROM
    SYSCOPY C:=ZSYS.SYS

`MZSYS` writes the IPL loader through the floppy driver: on a disk in
the MZ layout the driver shows the boot track as reserved track 3
(8 sectors of 512 bytes, not complemented) and maps reserved tracks 0-2
to cylinder 0 side 0 and cylinder 1, so the 27 sectors of the system
image do not touch the boot track. The data area is the same as in
Lamac's CP/M, so the disks are interchangeable.
