"""Stage 5: formatting floppies (DIODEFMED / DIOFORMAT in mzfd.asm, MZFMT.COM).

The system boots from a boot disk in drive 0 (as run_ipl.py, MZFMT.COM and MZSYS.COM on it). Drive 1 holds a disk
in the PC layout (9 x 512 also at cylinder 0 / side 1) with a file on it:
- MZFMT C: formats it in the MZ layout: afterwards DIR C: is empty, the DSK has the boot track of 16 x 256 at
  cylinder 0 / side 1 and 9 x 512 with Lamac's interleave elsewhere;
- MZSYS C: accepts the new disk (it needs the boot track) and PIP writes a file that cpmtools read back on the host;
- MZFMT C: /PC formats it back without the boot track, MZSYS then refuses it.

    python mzdev/tests/emu/run_fmt.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from mzdsk import Dsk, mkboot, put_files, SKEW9  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_ipl  # noqa: E402

DSK = os.path.join(WORK, 'dsk')
BOOT = os.path.join(DSK, 'fmt_boot.dsk')
TGT = os.path.join(DSK, 'fmt_tgt.dsk')
BIN = os.path.join(ROOT, 'Binary')
CPMTOOLS = os.path.join(ROOT, 'Tools', 'cpmtools')

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def mzfmt(emu, sym, args):
    """Run MZFMT with the answer Y, return the screen lines at the end."""
    run_console.type_text(emu, 'mzfmt %s\r' % args)
    run_console.wait_for(emu, sym, '(Y/N)', 600)
    run_console.type_text(emu, 'y')
    return run_console.run_cmd(emu, sym, '', 6000)


def layout(path):
    """(sector sizes at cylinder 0 / side 1, sector order at cylinder 5 / side 0) of the DSK."""
    d = Dsk.load(path)
    return [len(s[6]) for s in d.tracks[(0, 1)]], [s[2] for s in d.tracks[(5, 0)]]


def main():
    os.makedirs(DSK, exist_ok=True)
    files = [(os.path.join(BIN, 'Apps', 'mzfmt.com'), 'MZFMT.COM'),
             (os.path.join(BIN, 'Apps', 'mzsys.com'), 'MZSYS.COM')]
    mkboot(720, open(os.path.join(BIN, 'mz800-ipl.bin'), 'rb').read(), os.path.join(BIN, 'MZ800_std.upd'),
           sysimg=open(os.path.join(BIN, 'ZSDOS', 'zsys_wbw.sys'), 'rb').read(), files=files).save(BOOT)
    tgt = Dsk.new(720)
    put_files(tgt, 720, [(os.path.join(BIN, 'Apps', 'mzsys.com'), 'OLD.COM')])
    tgt.save(TGT)
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', fdd={0: BOOT, 1: TGT}, fdd_storage={1: 'cached'}) as emu:
        run_ipl.ipl_boot(emu, sym, 'boot disk')
        lines = run_console.run_cmd(emu, sym, 'dir c:')
        check(any('OLD     .COM' in l for l in lines), 'the target disk holds a file before formatting')
        lines = mzfmt(emu, sym, 'c:')
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-300:])
        check(any('Done.' in l for l in lines), 'MZFMT C: formats the disk (MZ layout)')
        lines = run_console.run_cmd(emu, sym, 'dir c:')
        check(any('No File' in l for l in lines[-3:]), 'DIR C: is empty after formatting')
        lines = run_console.run_cmd(emu, sym, 'mzsys c:')
        check(any(l.startswith('Done.') for l in lines), 'MZSYS accepts the freshly formatted disk')
        run_console.run_cmd(emu, sym, 'b:pip c:new.com=a:mzfmt.com', 3000)
    sizes, order = layout(TGT)
    check(sizes == [256] * 16, 'cylinder 0 / side 1 is the boot track 16 x 256 (%s)' % sizes)
    check(order == SKEW9, 'data tracks: 9 x 512, interleave %s' % order)
    img = TGT + '.img'
    with open(img, 'wb') as f:
        f.write(Dsk.load(TGT).to_raw())
    out = os.path.join(DSK, 'fmt_get.bin')
    if os.path.exists(out):
        os.remove(out)
    subprocess.run([os.path.join(CPMTOOLS, 'cpmcp.exe'), '-f', 'wbw_fd720', img, '0:new.com', out], cwd=CPMTOOLS,
                   capture_output=True)
    got = open(out, 'rb').read() if os.path.exists(out) else b''
    ref = open(os.path.join(BIN, 'Apps', 'mzfmt.com'), 'rb').read()     # CP/M rounds the size up to 128 B
    check(got[:len(ref)] == ref and len(got) == (len(ref) + 127) // 128 * 128,
          'cpmtools read the file written on the formatted disk')
    with Emu(memext='PEHU', fdd={0: BOOT, 1: TGT}, fdd_storage={1: 'cached'}) as emu:
        run_ipl.ipl_boot(emu, sym, 'boot disk')
        lines = mzfmt(emu, sym, 'c: /pc')
        check(any('Done.' in l for l in lines), 'MZFMT C: /PC formats the disk (PC layout)')
        lines = run_console.run_cmd(emu, sym, 'mzsys c:')
        check(any('NO MZ BOOT TRACK' in l for l in lines), 'MZSYS refuses the PC layout')
    sizes, _ = layout(TGT)
    check(sizes == [512] * 9, 'cylinder 0 / side 1 is 9 x 512 in the PC layout (%s)' % sizes)


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
