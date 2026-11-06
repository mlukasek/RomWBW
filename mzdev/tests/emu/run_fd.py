"""Stage 4: MZ-800 floppy driver (mzfd.asm), double density, in the emulator.

Drive 0 holds a copy of Lamac's CP/M 4.1 program disk (720K, boot track at cylinder 0 / side 1), drive 1 a blank
720K disk made by mzdsk.py. The system starts through the Unicard loader (as run_loader.py), then ZSDOS:
- the device list shows FD0 and FD1 (3.5" floppies), ZSDOS maps them to drives;
- DIR of drive 0 shows the files of the Lamac disk (MID_FD720 has the same DPB as Lamac's 720K);
- PIP copies two files from the Lamac disk to the blank one (new names: ZSDOS would find the R/O originals on A:
  through its path), a program from the floppy runs;
- after the emulator exits (it writes the images back), cpmtools on the host read the copied files from the second
  disk (mzdsk.py toraw + wbw_fd720) and they equal the originals from the Lamac disk;
- the motor goes off some seconds after the last access.

    python mzdev/tests/emu/run_fd.py
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
from mzdsk import Dsk  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

LAMAC_PRG = os.path.join(ROOT, '..', 'Martin-MZ-FDC', 'work', 'emu', 'prg41.dsk')
DSK = os.path.join(WORK, 'dsk')
FD0 = os.path.join(DSK, 'fd0.dsk')
FD1 = os.path.join(DSK, 'fd1.dsk')
CPMTOOLS = os.path.join(ROOT, 'Tools', 'cpmtools')
FILES = [('PIP.COM', 'LPIP.COM'), ('DUMP.COM', 'LDUMP.COM')]     # Lamac's file, its copy

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def cpm_get(dsk, name):
    """File `name` from the DSK through cpmtools (wbw_fd720 on the raw CP/M view), None if missing."""
    img = dsk + '.img'
    with open(img, 'wb') as f:
        f.write(Dsk.load(dsk).to_raw())
    out = os.path.join(DSK, 'get.bin')
    if os.path.exists(out):
        os.remove(out)
    subprocess.run([os.path.join(CPMTOOLS, 'cpmcp.exe'), '-f', 'wbw_fd720', img, '0:' + name.lower(), out],
                   cwd=CPMTOOLS, capture_output=True)
    return open(out, 'rb').read() if os.path.exists(out) else None


def main():
    os.makedirs(DSK, exist_ok=True)
    shutil.copyfile(LAMAC_PRG, FD0)
    Dsk.new(720).save(FD1)
    run_loader.prepare_sd()
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', unicard_sd=run_loader.SD, fdd={0: FD0, 1: FD1}, fdd_storage='cached') as emu:
        run_loader.start_loader(emu)
        lines = run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        screen = '\n'.join(lines)
        check('MZFD: IO=0xD8 UNITS=2' in screen.replace('\n', ' ') or 'FD0:' in screen, 'MZFD units in the boot list')
        print('\n'.join(l.rstrip() for l in lines if 'FD' in l))
        run_console.type_text(emu, 'z\r')
        lines = run_console.wait_for(emu, sym, 'A>')
        print('\n'.join(l.rstrip() for l in lines if ':=' in l))
        drv = {}
        for unit in (0, 1):
            found = [l.strip()[0] for l in lines if ('=FD%d:' % unit) in l]
            drv[unit] = found[0].lower() if found else None
        check(drv[0] and drv[1], 'ZSDOS maps FD0 and FD1 to drives %s' % drv)
        if not (drv[0] and drv[1]):
            return
        d0, d1 = drv[0], drv[1]
        lines = run_console.run_cmd(emu, sym, 'dir %s:' % d0)
        screen = '\n'.join(lines)
        print('\n'.join(l.rstrip() for l in lines[-12:]))
        check('PIP     .COM' in screen and 'FORMAT4 .COM' in screen, 'DIR of the Lamac disk shows its files')
        for name, copy in FILES:
            run_console.run_cmd(emu, sym, 'pip %s:%s=%s:%s' % (d1, copy.lower(), d0, name.lower()))
        lines = run_console.run_cmd(emu, sym, 'dir %s:' % d1)
        after = '\n'.join(lines[max(i for i, l in enumerate(lines) if l.startswith('A>dir')):])
        print(after)
        check(all(('%-8s.%s' % tuple(c.split('.'))) in after for _, c in FILES), 'DIR of the second disk shows the copies')
        # a program from the floppy runs: the copied DUMP dumps itself, the last line is at 0C70h (3200 B). Lamac's
        # DUMP opens the file on the current drive only.
        prompt = d1.upper() + '>'
        run_console.run_cmd(emu, sym, d1 + ':', prompt=prompt)
        lines = run_console.run_cmd(emu, sym, 'ldump ldump.com', 3000, prompt=prompt)
        print('\n'.join(l.rstrip() for l in lines[-4:]))
        check(any(l.startswith('0C70 ') for l in lines), 'DUMP.COM runs from the floppy')
        run_console.run_cmd(emu, sym, 'a:')
        on = run_hbios.bios_byte(emu, sym['MZFD_MOTON'])
        emu.run(250)                         # 5 s, the motor goes off after 3 s
        off = run_hbios.bios_byte(emu, sym['MZFD_MOTON'])
        check(on == 1 and off == 0, 'motor on after the access (%d), off 5 s later (%d)' % (on, off))
    for name, copy in FILES:
        src, dst = cpm_get(FD0, name), cpm_get(FD1, copy)
        check(src is not None and dst == src, '%s on the second disk equals %s of the Lamac disk (%s B)'
              % (copy, name, len(dst) if dst else None))


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
