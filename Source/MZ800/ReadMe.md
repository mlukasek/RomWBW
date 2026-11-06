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
