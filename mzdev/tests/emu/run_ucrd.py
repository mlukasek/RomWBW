"""Stage 3: Unicard RAM disk (ucrd.asm) with a 16 MB image.

The emulator's MZ-1R18 (SRAM, 16M, same ports $E9-$EB) stands in for the Unicard RAM disk. The image is a 16 MB
file filled with $E5 (two empty hd1k slices). The system is started through the Unicard loader. Checks:
- the device list shows UCRD0 (RAM disk, 16 MB), ZSDOS maps both slices to drives;
- PIP copies files to both slices, DIR shows them;
- after the emulator exits (it saves the SRAM image then), cpmtools on the host finds the files in the raw image
  (mzdev/tools/diskdefs: mz_ucrd_0, mz_ucrd_1).

    python mzdev/tests/emu/run_ucrd.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from vramtext import screen_text  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

IMG = os.path.join(WORK, 'ucrd16.img')
TOOLS = os.path.join(ROOT, 'mzdev', 'tools')
CPMLS = os.path.join(ROOT, 'Tools', 'cpmtools', 'cpmls.exe')

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def cpmls(fmt):
    r = subprocess.run([CPMLS, '-f', fmt, IMG], cwd=TOOLS, capture_output=True, text=True)
    return (r.stdout + r.stderr).upper()


def main():
    run_loader.prepare_sd()
    with open(IMG, 'wb') as f:
        f.write(b'\xE5' * (16 * 1024 * 1024))
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', unicard_sd=run_loader.SD, ramdisk=IMG) as emu:
        run_loader.start_loader(emu)
        lines = run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        screen = '\n'.join(lines)
        check('UCRD0:' in screen, 'UCRD0 in the device list')
        print('\n'.join(l.rstrip() for l in lines if 'UCRD' in l or 'Unit' in l))
        run_console.type_text(emu, 'z\r')
        lines = run_console.wait_for(emu, sym, 'A>')
        screen = '\n'.join(lines)
        check('=UCRD0:0' in screen and '=UCRD0:1' in screen, 'ZSDOS maps UCRD0:0 and UCRD0:1')
        print('\n'.join(l.rstrip() for l in lines if ':=' in l))
        drv0 = [l.strip()[0] for l in lines if '=UCRD0:0' in l]
        drv1 = [l.strip()[0] for l in lines if '=UCRD0:1' in l]
        if drv0 and drv1:
            d0, d1 = drv0[0].lower(), drv1[0].lower()
            # new names: with the same name ZSDOS finds the R/O original on A: through its path and PIP asks
            run_console.run_cmd(emu, sym, 'pip %s:p1.com=a:pip.com' % d0)
            run_console.run_cmd(emu, sym, 'pip %s:z1.com=a:zde.com' % d1)
            run_console.run_cmd(emu, sym, 'dir %s:' % d0)
            lines = run_console.run_cmd(emu, sym, 'dir %s:' % d1)
            screen = '\n'.join(lines)
            print('\n'.join(l.rstrip() for l in lines[-10:]))
            check('P1      .COM' in screen and 'Z1      .COM' in screen, 'DIR shows the copied files on both slices')
            # the copy runs: P1 (PIP) copies itself back from the RAM disk
            lines = run_console.run_cmd(emu, sym, '%s:p1 %s:p2.com=%s:p1.com' % (d0, d0, d0))
            lines = run_console.run_cmd(emu, sym, 'dir %s:' % d0)
            check('P2      .COM' in '\n'.join(lines), 'the copy of PIP runs from the Unicard RAM disk')
    out0, out1 = cpmls('mz_ucrd_0'), cpmls('mz_ucrd_1')
    check('P1.COM' in out0 and 'P2.COM' in out0, 'cpmtools finds P1.COM, P2.COM in slice 0 of the image: %s'
          % out0.split())
    check('Z1.COM' in out1, 'cpmtools finds Z1.COM in slice 1 of the image file: %s' % out1.split())


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
