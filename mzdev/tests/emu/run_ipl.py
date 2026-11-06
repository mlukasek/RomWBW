"""Stage 5: boot from a floppy (IPL boot track, Source/MZ800/mzipl.asm) and MZSYS.COM.

1. A boot disk made by `mzdsk.py mkboot` (MZ layout 720K: IPL loader on the boot track, ROMWBW.ROM = the full
   .rom, ZSDOS in the reserved tracks, ZSYS.SYS, ROMWBW.UPD and MZSYS.COM as files) in drive 0. After reset the
   MZ-800 ROM starts the IPL loader: its messages on the MZ-700 screen, then the HBIOS boot loader. Its disk boot
   from FD0 (unit 1) starts ZSDOS from the reserved tracks with A: = FD0.
2. In that system a blank disk in the MZ layout (as Lamac's CP/M formats it) in drive 1 is made bootable as a user
   would do it: MZSYS C:, COPY C:ROMWBW.ROM=A:ROMWBW.UPD, SYSCOPY C:=A:ZSYS.SYS. MZSYS refuses a disk without
   the MZ boot track (PC layout). (Not PIP: ROMWBW.ROM is also on A:, ZSDOS finds it through its path when PIP
   renames ROMWBW.$$$ and PIP ends without a word, the copy stays as ROMWBW.$$$.)
3. The new disk boots in drive 0 of a fresh emulator, up to ZSDOS from it.

    python mzdev/tests/emu/run_ipl.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from mzdsk import Dsk, mkboot  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

DSK = os.path.join(WORK, 'dsk')
BOOT = os.path.join(DSK, 'ipl_boot.dsk')
NEW = os.path.join(DSK, 'ipl_new.dsk')
PC = os.path.join(DSK, 'ipl_pc.dsk')
BIN = os.path.join(ROOT, 'Binary')

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def ipl_boot(emu, sym, label):
    """Reset with the disk in drive 0, follow the IPL loader to the HBIOS boot loader, boot FD0 (unit 1)."""
    emu.reset()
    seen = ''
    for _ in range(40):
        emu.run(25)
        seen = '\n'.join(run_loader.text700(emu))
        if 'LOADING' in seen:
            break
    check('ROMWBW FLOPPY LOADER FOR SHARP MZ-800' in seen and 'MEMEXT: PEHU 512K' in seen,
          '%s: IPL loader runs (title and MemExt on the MZ-700 screen)' % label)
    lines = run_console.wait_for(emu, sym, 'Boot [H=Help]:', 2000, 20)
    check(any('Boot [H=Help]:' in l for l in lines), '%s: HBIOS boot loader after loading the image' % label)
    run_console.type_text(emu, '1\r')
    lines = run_console.wait_for(emu, sym, 'A>', 600)
    screen = '\n'.join(lines)
    check('A:=FD0:0' in screen and 'ZSDOS v1.1' in screen, '%s: disk boot from FD0, ZSDOS with A: = FD0' % label)
    return lines


def main():
    os.makedirs(DSK, exist_ok=True)
    files = [(os.path.join(BIN, 'ZSDOS', 'zsys_wbw.sys'), 'ZSYS.SYS'),
             (os.path.join(BIN, 'MZ800_std.upd'), 'ROMWBW.UPD'),
             (os.path.join(BIN, 'Apps', 'mzsys.com'), 'MZSYS.COM')]
    mkboot(720, open(os.path.join(BIN, 'mz800-ipl.bin'), 'rb').read(), os.path.join(BIN, 'MZ800_std.rom'),
           sysimg=open(os.path.join(BIN, 'ZSDOS', 'zsys_wbw.sys'), 'rb').read(), files=files).save(BOOT)
    Dsk.new(720, lamac=True).save(NEW)
    Dsk.new(720).save(PC)
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', fdd={0: BOOT, 1: PC}) as emu:
        ipl_boot(emu, sym, 'boot disk')
        lines = run_console.run_cmd(emu, sym, 'dir')
        screen = '\n'.join(lines)
        check('ROMWBW  .ROM' in screen and 'MZSYS   .COM' in screen, 'DIR A: shows the files of the boot disk')
        lines = run_console.run_cmd(emu, sym, 'mzsys c:')
        check(any('NO MZ BOOT TRACK' in l for l in lines), 'MZSYS refuses a disk in the PC layout')
    with Emu(memext='PEHU', fdd={0: BOOT, 1: NEW}, fdd_storage={1: 'cached'}) as emu:
        ipl_boot(emu, sym, 'boot disk')
        lines = run_console.run_cmd(emu, sym, 'mzsys c:')
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-300:])
        check(any(l.startswith('Done.') for l in lines), 'MZSYS writes the boot track of C:')
        lines = run_console.run_cmd(emu, sym, 'b:copy c:romwbw.rom=a:romwbw.upd', 6000)
        check(any('0 Errors' in l for l in [x for x in lines if x.strip()][-3:]),
              'COPY puts the image on C: and verifies it')
        run_console.type_text(emu, 'b:syscopy c:=a:zsys.sys\r')
        run_console.wait_for(emu, sym, '(Y/N)?', 600)
        run_console.type_text(emu, 'y')
        lines = run_console.run_cmd(emu, sym, '', 1500)
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-300:])
        lines = run_console.run_cmd(emu, sym, 'dir c:')
        check(any('ROMWBW  .ROM' in l for l in [x for x in lines if x.strip()][-3:]), 'the image is on C:')
    d = Dsk.load(NEW)
    ipl = bytes(255 - b for r in range(1, 17) for b in d.sector(0, 1, r))
    ref = open(os.path.join(BIN, 'mz800-ipl.bin'), 'rb').read()
    check(ipl[:256] == ref[:256] and ipl[256 + 18:] == ref[256 + 18:],
          'the boot track holds the IPL loader (complemented, as the ROM reads it)')
    with Emu(memext='PEHU', fdd={0: NEW}) as emu:
        ipl_boot(emu, sym, 'new disk')
        lines = run_console.run_cmd(emu, sym, 'dir')
        check(any('ROMWBW  .ROM' in l for l in lines), 'DIR A: of the new boot disk')


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
