"""BLANK history of the MZ-800 keyboard driver (mzkbd.asm): BLANK = older line, SHIFT+BLANK = newer line.

Boots Binary/MZ800_std.upd (as run_console.py) into ZSDOS and checks on the prompt line:
- BLANK steps back through the entered lines, newest first; past the oldest one nothing changes (no glued lines as
  in Lamac's CP/M);
- SHIFT+BLANK steps forward again, past the newest one the line is empty;
- a line entered twice in a row is kept once;
- BLANK replaces a half typed line;
- the recalled line runs with CR and becomes the newest one;
- when the 256 byte history overflows, only whole lines are recalled (the oldest cut off line is skipped).

    python mzdev/tests/emu/run_blank.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
from mzemu import Emu  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from vramtext import screen_text  # noqa: E402
import run_hbios  # noqa: E402
from run_console import wait_for, run_cmd, type_text  # noqa: E402

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def prompt(emu, sym):
    emu.run(10)
    return [l for l in screen_text(emu, sym) if l.startswith('A>')][-1].rstrip()


def blank(emu, sym, shift=False):
    if shift:
        emu.call('input_press_key', {'key': 'SHIFT'})
        emu.run(2)
    emu.key('BLANK', 2, 3)
    if shift:
        emu.call('input_release_key', {'key': 'SHIFT'})
        emu.run(3)
    return prompt(emu, sym)


def main():
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU') as emu:
        run_hbios.boot(emu, open(run_hbios.UPD, 'rb').read())
        wait_for(emu, sym, 'Boot [H=Help]:')
        type_text(emu, 'z\r')
        wait_for(emu, sym, 'A>')
        for cmd in ('a1', 'b22', 'b22', 'c333'):
            run_cmd(emu, sym, cmd, 300)
        got = [blank(emu, sym) for _ in range(5)]       # the oldest line is the 'z' typed at the boot loader
        check(got == ['A>c333', 'A>b22', 'A>a1', 'A>z', 'A>z'],
              'BLANK steps back, b22 once, stays at the oldest: %s' % got)
        got = [blank(emu, sym, True) for _ in range(5)]
        check(got == ['A>a1', 'A>b22', 'A>c333', 'A>', 'A>'], 'SHIFT+BLANK steps forward to an empty line: %s' % got)
        type_text(emu, 'zz')
        got = blank(emu, sym)
        check(got == 'A>c333', 'BLANK replaces a half typed line: %r' % got)
        got = blank(emu, sym)
        lines = [l.rstrip() for l in run_cmd(emu, sym, '', 300) if l.strip()]
        check(got == 'A>b22' and lines[-3:] == ['A>b22', 'No File', 'A>'],    # ZSDOS: unknown command = No File
              'the recalled line runs: %s' % lines[-3:])
        got = [blank(emu, sym) for _ in range(2)]
        check(got == ['A>b22', 'A>c333'], 'it is the newest line now: %s' % got)
        # overflow: 12 lines of 30 characters = 12 * 31 bytes; 8 whole lines fit into 256 bytes
        for _ in range(40):
            emu.key('DEL', 2, 2)
        longs = ['l%02d-%s' % (i, 'x' * 26) for i in range(1, 13)]
        for cmd in longs:
            run_cmd(emu, sym, cmd, 600)
        got = [blank(emu, sym)[2:] for _ in range(10)]
        want = [longs[i] for i in range(11, 3, -1)] + [longs[4], longs[4]]
        check(got == want, 'after the overflow only whole lines (l12..l05), then it stays: %s'
              % [g[:3] for g in got])


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
