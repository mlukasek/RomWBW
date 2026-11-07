"""Stage 7: CP/M 3 and ZPM3 from a floppy.

For each system a 1.44M boot disk in Lamac's HD format is made by mzdsk.py mkboot: the IPL loader and the RomWBW
image (ROMWBW.ROM = MZ800_std.upd), the loader of the system in the reserved tracks (CPMLDR.SYS / ZPMLDR.SYS, as
SYSCOPY puts it there) and the files of the RomWBW floppy image definition (Source/Images/fd_cpm3.txt,
fd_zpm3.txt) in their user areas. The boot loader's disk boot from FD0
starts the loader, which loads CPM3.SYS (banked, the RomWBW banks of MemExt) and the CCP: the prompt comes and
DIR lists the disk. The TPA is checked with the size printed by the loader.

    python mzdev/tests/emu/run_cpm3.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from vramtext import screen_text  # noqa: E402
from mzdsk import mkboot, image_def  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

DSK = os.path.join(WORK, 'dsk')
BIN = os.path.join(ROOT, 'Binary')
IMAGES = os.path.join(ROOT, 'Source', 'Images')
SYSTEMS = {'CP/M 3': ('cpm3.dsk', 'fd_cpm3.txt'), 'ZPM3': ('zpm3.dsk', 'fd_zpm3.txt')}


failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def boot(label, dskname, deffile):
    path = os.path.join(DSK, dskname)
    ldr, files = image_def(os.path.join(IMAGES, deffile), 1200 * 1024)   # the ZPM3 set does not fit 1.44M
    mkboot(1440, open(os.path.join(BIN, 'mz800-ipl.bin'), 'rb').read(), os.path.join(BIN, 'MZ800_std.upd'),
           sysimg=open(ldr, 'rb').read(), files=files).save(path)
    print('--- %s: %d files on a 1.44M boot disk' % (label, len(files)))
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', fdd={0: path}) as emu:
        emu.reset()
        lines = run_console.wait_for(emu, sym, 'Boot [H=Help]:', 2500, 20)
        check(any('Boot [H=Help]:' in l for l in lines), '%s: IPL boot up to the boot loader' % label)
        run_console.type_text(emu, '1\r')
        text = []
        for _ in range(0, 1500, 10):              # the prompt: A> (CP/M 3) or A0> (ZPM3)
            emu.run(10)
            text = [l.rstrip() for l in screen_text(emu, sym) if l.strip()]
            if text and text[-1].startswith('A') and text[-1].endswith('>'):
                break
        print('\n'.join(text[-12:]))
        check(text and text[-1].endswith('>'), '%s: boots to the prompt %s' % (label, text[-1] if text else None))
        tpa = [l for l in text if 'TPA' in l]
        check(bool(tpa), '%s: TPA reported: %s' % (label, tpa[-1].strip() if tpa else None))
        lines = run_console.run_cmd(emu, sym, 'dir', 600, prompt=text[-1] if text else 'A>')
        check(any('CPM3' in l for l in lines), '%s: DIR shows CPM3.SYS' % label)
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-400:])


def main():
    os.makedirs(DSK, exist_ok=True)
    for label, (dskname, deffile) in SYSTEMS.items():
        boot(label, dskname, deffile)


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
