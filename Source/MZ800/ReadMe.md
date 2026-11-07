# SHARP MZ-800

RomWBW runs on the SHARP MZ-800 with a 512K MemExt memory expansion
(PEHU or Luftner board, detected at startup). The image is ROM-less:
a loader puts it into MemExt RAM and starts HBIOS. It is built as
`MZ800_std` (`Source/HBIOS/Config/MZ800_std.asm`, platform `PLT_MZ800`).

## Hardware

| Part | Use |
|---|---|
| MemExt 512K (PEHU or Luftner) | all RAM: banks $80-$8F (`MM_MZ800`), required |
| GDG (640x200) | console 80x25 (`mzv.asm`), font from the ROM image |
| keyboard (8255) | console input (`mzkbd.asm`), scanned on the tick |
| Z80 PIO PA5 (VBLANK) | 50 Hz system tick (`TM_MZV`, interrupt mode 2) |
| floppy interface (WD279x, MB8876, WD177x) | `mzfd.asm`, `FD0:`-`FD3:` |
| Unicard | RTC (`ucrtc.asm`), RAM disk (`ucrd.asm`), SD card files (`UC.COM`), boot loader |

- **MemExt** (port $E7, the page of the address space in A12-A15, the
  bank as data): PEHU has 8K banks, Luftner 4K banks. The proxy bank
  select is patched at startup for the board found. Without MemExt the
  loaders stop with a message and HBIOS halts with a red border.
- **The ROM and VRAM** are mapped out (`OUT ($E0)`, `OUT ($E1)`,
  `IN ($E1)`). The console maps VRAM and the character ROM in for a
  moment with interrupts off, so its code stays above $2000.

## Console

- **640x200 mono**, 80x25 characters 8x8 (the RomWBW font), hardware
  scroll, the cursor is an inverted bottom line. VDARES (called at every
  warm boot) only programs the GDG again, the screen stays.
- **Keyboard:** letters lower case, SHIFT upper case, ALPHA is Caps
  Lock. Cursor keys, INST/DEL, F1-F5 (with SHIFT F6-F10) give the RomWBW
  key codes.
- **BLANK** on an empty line types the last entered line again (as in
  Lamac's CP/M for the MZ-800). The driver follows the characters it
  returns, so this works in every program reading lines.

## Disks

| Unit | Device | Notes |
|---|---|---|
| `MD0:` | RAM disk 256K in MemExt | filled from the `.rom` image, see below |
| `FD0:`-`FD3:` | floppies (`MZFDCNT`, `MZFD0TYPE`...) | see below |
| `UCRD0:` | Unicard RAM disk, image file on the SD card | 16M = two hd1k slices, 4M = RAM floppy |

### Floppy driver (`mzfd.asm`)

- **Double density** is transferred by polling (87 T-states per byte).
  **High density** (`MZFDHD`, the HD modification: ports $DE/$DF) uses
  the DRQ interrupt as Lamac's CP/M does: IM 1 with a 7 byte ISR at
  $0038 of the HBIOS bank, the VBLANK tick is off during such a command.
- **Media:** RomWBW `MID_FD720`, `MID_FD360`, `MID_FD144`, `MID_FD120`,
  and Lamac's HD formats `MID_MZ144`, `MID_MZ120` (4K blocks, 4
  reserved tracks). The data area of Lamac's 720K and 360K is the same
  as FD720/FD360, so these disks work in both systems.
- **MZ layout:** on Lamac's disks cylinder 0, side 1 is the IPL boot
  track (16 x 256, double density). The driver maps the reserved tracks
  so that the 27 sectors of a system image (`SYSCOPY`) miss it: logical
  track 0 = cylinder 0 side 0, 1 = cylinder 1 side 0, 2 = cylinder 1
  side 1, 3 = the boot track (8 sectors of 512, as the ROM sees it).
- **DIODEFMED** (bit 7 of E: MZ layout) and **DIOFORMAT** (double
  density) are implemented, used by `MZFMT.COM`.
- **Options:** step rate `MZFDSTEP`, spin up `MZFDSPIN`, head settle
  `MZFDSETL`, motor off `MZFDMOTO`.

## Boot

### Unicard loader (`mz800-ldr.mzf`)

1. Copy `Binary/mz800-ldr.mzf` and `Binary/MZ800_std.rom` to the Unicard
   SD card, into the same directory or the image into `/romwbw/`.
2. Start `mz800-ldr.mzf` from the Unicard Manager, or name it in
   `/unicard/mzfloader.cfg` to start it at power on (Q at the boot menu of
   the MZ-800 boots the QuickDisk of the Unicard, its loader SC3SROM at
   $1200-$12A5 starts that MZF; so `mz800-ldr.mzf` loads at $2000).

The loader detects MemExt (without it, it stops with a message),
moves itself into the common bank, reads the image sequentially
(Unicard firmware 0.26 has no working SEEK) into banks $80.. and jumps
to HBIOS. The full `.rom` image also fills the RAM disk with the RomWBW
utilities; the `.upd` image (first 128K) leaves it empty.

### Floppy boot (`mz800-ipl.bin`, `MZSYS.COM`)

A floppy in one of the formats of Lamac's CP/M for the MZ-800 (720K,
360K, HD 1.44M or 1.2M with the HD modification) in the MZ layout
boots RomWBW from drive 0 at power on:

- the boot track holds `mz800-ipl.bin`: the IPLPRO header and a loader
  that detects MemExt, reads the CP/M directory of the disk and loads
  the file `ROMWBW.ROM` (user 0) into banks $80.. like the Unicard
  loader, then starts HBIOS;
- `ROMWBW.ROM` is `MZ800_std.rom` (fills the RAM disk too) or
  `MZ800_std.upd` (loads three times quicker, empty RAM disk);
- optionally a CP/M system in the reserved tracks (`SYSCOPY`) lets the
  boot loader boot the floppy itself (disk unit of FD0), A: is then the
  floppy. CP/M 3 and ZPM3 boot this way too (`CPMLDR.SYS`,
  `ZPMLDR.SYS`), banked with a 60K TPA.

On a RomWBW system, a disk formatted by Lamac's CP/M or `MZFMT` is made
bootable with:

    MZSYS C:
    COPY C:ROMWBW.ROM=...MZ800_STD.ROM
    SYSCOPY C:=ZSYS.SYS

(PIP fails to copy `ROMWBW.ROM` when a file of that name is on A:,
because ZSDOS finds it through its path when PIP renames the copy.)

## Utilities (`Binary/Apps`)

The `.rom` image fills drive A: (`MD0:`) with the files of the standard
256K ROM disk, without the tools for other hardware (`FDU`: 765 floppy
controllers, `FLASH`: flash ROM, `RTC`: DS1302 only), plus the
utilities below and `WDATE` (shows and sets the date and time of the
Unicard RTC through HBIOS). `Source/MZ800/Build.cmd` makes this disk
and puts the `.rom` images together again after the HBIOS build.

| Program | Use |
|---|---|
| `WDATE [YY MM DD HH MM SS]` | show or set the date and time |
| `MZSYS D: [FILE.EXT]` | write the IPL loader to the boot track of a floppy (CP/M 2.2) |
| `MZFMT D: [/360] [/PC]` | format a double density floppy, MZ layout (or `/PC` without the boot track) |
| `UC DIR [PATH]` | list a directory of the Unicard SD card |
| `UC CD PATH` | change the current SD directory |
| `UC GET SDFILE [D:FILE]` | copy a file from the SD card |
| `UC PUT D:FILE [SDFILE]` | copy a file to the SD card |
| `UC MOUNT IMAGE` | image file for the Unicard RAM disk (restart afterwards) |

## Limits

- No high density formatting yet: format HD disks with Lamac's FORMAT4.
- The system tick stops during high density floppy commands.
- The boot messages of the modules before the console (CPU, memory,
  RTC) are not shown.
- `UC` reads and writes files sequentially only; the Unicard firmware
  0.26 has no working SEEK.
- Programs that use the memory or the BIOS of Lamac's CP/M do not work
  under RomWBW. Its `TIME` reads its clock at $EA40 (CBIOS code under
  RomWBW, do not set the time with it); use `WDATE` instead. `UNIUTIL`
  (Unicard utility, Turbo Pascal 3) needs the BDOS at $D942 or higher:
  it runs under CP/M 3, under CP/M 2.2 it stops with "Not enough
  memory" (use `UC` there).
- Lamac's CP/M takes the RAM disk on the same ports as its drive `E:`
  and formats it when it boots (seen in the emulator): the first 4K,
  the boot area of slice 0, is overwritten. Give Lamac's CP/M its own
  RAM disk image (`UC MOUNT`).
