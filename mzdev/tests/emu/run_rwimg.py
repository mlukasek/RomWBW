"""Stage 7: the disk images built by RomWBW itself (Binary/hd1k_*.img, Binary/fd144_*.img) on the MZ-800.

1. The Unicard RAM disk image (16 MB) is hd1k_cpm3.img followed by hd1k_zpm3.img: two hd1k slices as UCRD0:0 and
   UCRD0:1. The boot loader boots CP/M 3 from slice 0 (unit 3) and ZPM3 from slice 1 (unit 3.1), banked, 60K TPA.
2. fd144_cpm3.img (RomWBW FD144 format, 80 x 2 x 18 x 512 without the MZ boot track) as a DSK in drive 0: the
   driver finds MID_FD144 and the boot loader boots CP/M 3 from the floppy (unit 1).

    python mzdev/tests/emu/run_rwimg.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from vramtext import screen_text  # noqa: E402
from mzdsk import Dsk  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

BIN = os.path.join(ROOT, 'Binary')
RAMDISK = os.path.join(WORK, 'rw_ucrd16.img')
FD144 = os.path.join(WORK, 'dsk', 'rw_fd144.dsk')

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def boot(emu, sym, cmd, label):
    """At the boot loader prompt: boot `cmd`, wait for a prompt ending with '>'. Returns the screen text lines."""
    run_console.type_text(emu, cmd + '\r')
    text = []
    for _ in range(0, 2000, 10):
        emu.run(10)
        text = [l.rstrip() for l in screen_text(emu, sym) if l.strip()]
        if text and text[-1].endswith('>') and not text[-1].endswith(cmd):
            break
    print('\n'.join(text[-8:]))
    check(any('60K TPA' in l for l in text) and text[-1].endswith('>'), '%s: boots, 60K TPA' % label)
    return text


def main():
    sym = load_lst(run_hbios.LST)
    with open(RAMDISK, 'wb') as f:
        for name in ('hd1k_cpm3.img', 'hd1k_zpm3.img'):
            f.write(open(os.path.join(BIN, name), 'rb').read())
    run_loader.prepare_sd()
    for cmd, label in (('3', 'CP/M 3 from UCRD0 slice 0'), ('3.1', 'ZPM3 from UCRD0 slice 1')):
        with Emu(memext='PEHU', unicard_sd=run_loader.SD, ramdisk=RAMDISK) as emu:
            run_loader.start_loader(emu)
            run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
            boot(emu, sym, cmd, label)
    raw = open(os.path.join(BIN, 'fd144_cpm3.img'), 'rb').read()
    d = Dsk.new(1440)
    d.from_raw(raw, 18)
    d.save(FD144)
    with Emu(memext='PEHU', unicard_sd=run_loader.SD, fdd={0: FD144}) as emu:
        run_loader.start_loader(emu)
        run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        boot(emu, sym, '1', 'CP/M 3 from fd144_cpm3.img in FD0')
        lines = run_console.run_cmd(emu, sym, 'dir', 600)
        check(any('CPM3' in l for l in lines), 'DIR of the RomWBW 1.44M floppy')


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
