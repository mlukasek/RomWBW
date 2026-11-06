"""Stage 6: high density floppies (mzfd.asm with MZFDHD: the DRQ interrupt, IM 1 ISR at $0038).

Drive 0 holds a copy of a 1.44M disk of Lamac's CP/M (Martin144.dsk: HD 18 x 512, 4K blocks, the IPL boot track
in DD), drive 1 a blank disk of the same format made by mzdsk.py. The system starts through the Unicard loader:
- media discovery finds MID_MZ144 (STAT: 1404K, 32 records per block, 72 sectors per track, 4 reserved tracks);
- DIR of drive 0 shows the files of Lamac's disk;
- ZSDOS COPY copies two files to drive 1 and verifies them;
- the system tick still runs after the disk work (the VBLANK interrupt is off during HD commands);
- after the emulator exits, cpmtools (mz_lamac144) read the copies from the image, equal to the originals;
- a 1.44M boot disk made by mzdsk.py mkboot boots: the IPL loader reads the HD data area (DRQ interrupt), the
  boot loader boots ZSDOS from its reserved tracks (HD), A: is the disk.

    python mzdev/tests/emu/run_hd.py
"""
import os
import shutil
import subprocess
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
import run_ipl  # noqa: E402

LAMAC_HD = os.path.join(ROOT, '..', 'MFDC800T', 'DSK', 'Martin144.dsk')
DSK = os.path.join(WORK, 'dsk')
FD0 = os.path.join(DSK, 'hd0.dsk')
FD1 = os.path.join(DSK, 'hd1.dsk')
BOOT = os.path.join(DSK, 'hd_boot.dsk')
TOOLS = os.path.join(ROOT, 'mzdev', 'tools')
CPMCP = os.path.join(ROOT, 'Tools', 'cpmtools', 'cpmcp.exe')
FILES = ['PIP.COM', 'TURBOED.COM']

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def cpm_get(dsk, name):
    """File `name` from a DSK in Lamac's 1.44M format through cpmtools, None if missing."""
    img = dsk + '.img'
    with open(img, 'wb') as f:
        f.write(Dsk.load(dsk).to_raw(18))
    out = os.path.join(DSK, 'hd_get.bin')
    if os.path.exists(out):
        os.remove(out)
    subprocess.run([CPMCP, '-f', 'mz_lamac144', img, '0:' + name.lower(), out], cwd=TOOLS, capture_output=True)
    return open(out, 'rb').read() if os.path.exists(out) else None


def main():
    os.makedirs(DSK, exist_ok=True)
    shutil.copyfile(LAMAC_HD, FD0)
    Dsk.new(1440, lamac=True).save(FD1)
    run_loader.prepare_sd()
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', unicard_sd=run_loader.SD, fdd={0: FD0, 1: FD1}, fdd_storage={1: 'cached'}) as emu:
        run_loader.start_loader(emu)
        run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        run_console.type_text(emu, 'z\r')
        lines = run_console.wait_for(emu, sym, 'A>')
        drv = {}
        for unit in (0, 1):
            found = [l.strip()[0] for l in lines if ('=FD%d:' % unit) in l]
            drv[unit] = found[0].lower() if found else None
        check(drv[0] and drv[1], 'ZSDOS maps FD0 and FD1 to drives %s' % drv)
        if not (drv[0] and drv[1]):
            return
        d0, d1 = drv[0], drv[1]
        lines = run_console.run_cmd(emu, sym, 'stat %s:dsk:' % d0)
        screen = '\n'.join(lines)
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-500:])
        check('1404: Kilobyte' in screen and '32: Records/ Block' in screen and '72: Sectors/ Track' in screen
              and '4: Reserved' in screen, "STAT: Lamac's 1.44M format (MID_MZ144)")
        lines = run_console.run_cmd(emu, sym, 'dir %s:' % d0)
        screen = '\n'.join(lines)
        check('PIP     .COM' in screen and 'TURBOED .COM' in screen, 'DIR of the HD disk shows its files')
        for name in FILES:
            lines = run_console.run_cmd(emu, sym, 'copy %s:=%s:%s' % (d1, d0, name.lower()), 3000)
            text = [l.rstrip() for l in lines if l.strip()]
            print('\n'.join(text[-3:]))
            check(any('0 Errors' in l for l in text[-3:]), 'COPY %s to the blank HD disk, verified' % name)
        t0 = int.from_bytes(emu.memext_read(sym['HB_TICKS'], 4), 'little')
        emu.run(100)
        t1 = int.from_bytes(emu.memext_read(sym['HB_TICKS'], 4), 'little')
        check(95 <= t1 - t0 <= 105, 'the system tick runs after HD work: %d ticks in 100 frames' % (t1 - t0))
    for name in FILES:
        src, dst = cpm_get(FD0, name), cpm_get(FD1, name)
        check(src is not None and dst == src, '%s on the second disk equals the original (%s B)'
              % (name, len(dst) if dst else None))
    # boot from an HD disk: the IPL loader reads the HD data area with the DRQ interrupt
    bin_ = os.path.join(ROOT, 'Binary')
    mkboot(1440, open(os.path.join(bin_, 'mz800-ipl.bin'), 'rb').read(), os.path.join(bin_, 'MZ800_std.upd'),
           sysimg=open(os.path.join(bin_, 'ZSDOS', 'zsys_wbw.sys'), 'rb').read(),
           files=[(os.path.join(ROOT, 'Source', 'RomDsk', 'ROM_256KB', 'STAT.COM'), 'STAT.COM')]).save(BOOT)
    with Emu(memext='PEHU', fdd={0: BOOT}) as emu:
        run_ipl.ipl_boot(emu, sym, 'HD boot disk')
        lines = run_console.run_cmd(emu, sym, 'stat a:dsk:')
        check(any('1404: Kilobyte' in l for l in lines), 'A: is the HD boot disk (1.44M, Lamac format)')
        lines = run_console.run_cmd(emu, sym, 'dir')
        check(any('ROMWBW  .ROM' in l for l in lines), 'DIR A: shows the image file')


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
