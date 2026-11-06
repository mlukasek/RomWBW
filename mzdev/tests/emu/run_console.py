"""Stage 2: console on the MZ-800 screen and keyboard.

Boots Binary/MZ800_std.upd (as run_hbios.py), then checks on the decoded screen text (tools/emu/vramtext.py):
- the boot loader prompt and the device list (TERM0 on MZV0, MD0 RAM disk);
- typing Z + CR boots ZSDOS with 54.0K TPA from the image to A>;
- DIR on the freshly formatted RAM disk;
- lines scroll (hardware scroll) without breaking the text.

    python mzdev/tests/emu/run_console.py [PEHU|LUFTNER] [--random] [--shot file.png]

--random fills MemExt RAM with random bytes at power-on (as real DRAM) instead of zeros.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
from mzemu import Emu  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from vramtext import screen_text  # noqa: E402
import run_hbios  # noqa: E402

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def wait_for(emu, sym, text, frames=600, step=10):
    """Run until `text` is on the screen; returns the screen lines (last state if not found)."""
    lines = []
    for _ in range(0, frames, step):
        emu.run(step)
        lines = screen_text(emu, sym)
        if any(text in line for line in lines):
            return lines
    return lines


def type_text(emu, text):
    names = {'\r': 'CR', ' ': 'SPACE'}
    for ch in text:
        emu.key(names.get(ch, ch.upper()), 2, 3)


def main():
    memext = 'PEHU'
    shot = None
    args = sys.argv[1:]
    if '--shot' in args:
        shot = args[args.index('--shot') + 1]
        del args[args.index('--shot'):args.index('--shot') + 2]
    fill = 'NULL'
    if '--random' in args:
        fill = 'RANDOM'
        args.remove('--random')
    if args:
        memext = args[0]
    print('--- MemExt %s, RAM fill %s' % (memext, fill))
    sym = load_lst(run_hbios.LST)
    with Emu(memext=memext, fill=fill) as emu:
        run_hbios.boot(emu, open(run_hbios.UPD, 'rb').read())
        lines = wait_for(emu, sym, 'Boot [H=Help]:')
        screen = '\n'.join(lines)
        check('Boot [H=Help]:' in screen, 'boot loader prompt on screen')
        check('TERM0:' in screen and 'MZV0:' in screen and 'Text,80x25' in screen, 'TERM0 on MZV0, 80x25 text')
        check('MD0:' in screen and '256KB' in screen, 'MD0 RAM disk 256KB')
        t0 = int.from_bytes(emu.memext_read(sym['HB_TICKS'], 4), 'little')
        emu.run(100)
        t1 = int.from_bytes(emu.memext_read(sym['HB_TICKS'], 4), 'little')
        check(95 <= t1 - t0 <= 105, 'system tick from VBLN: %d ticks in 100 frames' % (t1 - t0))
        type_text(emu, 'z\r')
        lines = wait_for(emu, sym, 'A>')
        screen = '\n'.join(lines)
        check('ZSDOS v1.1, 54.0K TPA' in screen, 'ZSDOS boots with 54.0K TPA')
        check(lines[-1].startswith('A>') or any(l.startswith('A>') for l in lines), 'A> prompt')
        type_text(emu, 'dir\r')
        lines = wait_for(emu, sym, 'No File', 300)
        check(any('No File' in l for l in lines), 'DIR on the empty RAM disk says No File')
        emu.key('X', 60, 5)                  # held 1.2 s: first repeat after 0.5 s, then every 3 ticks
        prompt = [l for l in screen_text(emu, sym) if l.startswith('A>')][-1]
        count = prompt.count('x')
        check(10 <= count <= 25, 'auto-repeat: X held 60 frames gives %d characters' % count)
        for _ in range(count):
            emu.key('DEL', 2, 2)             # DEL = backspace: erase them again
        prompt = [l for l in screen_text(emu, sym) if l.startswith('A>')][-1]
        check(prompt.rstrip() == 'A>', 'DEL (backspace) erases the line')
        emu.key('BLANK', 3, 5)               # BLANK on an empty line: the last command again (as in Lamac's CP/M)
        emu.run(10)
        prompt = [l for l in screen_text(emu, sym) if l.startswith('A>')][-1]
        check(prompt.rstrip() == 'A>dir', 'BLANK recalls the last command: %r' % prompt.rstrip())
        type_text(emu, '\r')
        lines = wait_for(emu, sym, 'A>', 100)
        check(sum(1 for l in lines if 'No File' in l) >= 2, 'the recalled DIR runs again')
        for _ in range(12):
            type_text(emu, '\r')
        lines = wait_for(emu, sym, 'A>', 100)
        prompts = sum(1 for l in lines if l.rstrip() == 'A>')
        check(prompts >= 12 and '?' not in ''.join(lines), 'scrolling keeps the text intact (%d prompts)' % prompts)
        print('\n'.join(l.rstrip() for l in lines))
        if shot:
            emu.screenshot(shot)


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
