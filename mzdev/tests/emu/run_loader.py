"""Stage 3: the Unicard loader Binary/mz800-ldr.mzf.

The emulated Unicard SD card is mzdev/work/sd with the image in /romwbw/MZ800_std.rom (the loader first tries the
current directory, which is / after reset, then /romwbw). The MZF is loaded at $1200 as the Unicard Manager does and
started. Checks:
- with PEHU and Luftner: loader messages, HBIOS boot loader prompt, the RAM disk filled from the .rom image (DIR shows
  the RomWBW utilities after booting ZSDOS);
- without MemExt: the loader stops with its message on the MZ-700 text screen;
- without the image file: the loader stops with its message.

    python mzdev/tests/emu/run_loader.py
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from vramtext import screen_text  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402

MZF = os.path.join(ROOT, 'Binary', 'mz800-ldr.mzf')
ROM = os.path.join(ROOT, 'Binary', 'MZ800_std.rom')
SD = os.path.join(WORK, 'sd')

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def text700(emu):
    """The MZ-700 mode text screen (40x25 display codes) as 25 strings (letters, digits, space, a few signs)."""
    codes = emu.region('vram_700_char', 0, 1000)
    signs = {0x00: ' ', 0x2E: '.', 0x4F: ':', 0x2F: ',', 0x2A: '-', 0x2D: '/', 0x68: '(', 0x69: ')', 0x61: '!',
             0x49: '?', 0x2B: '='}

    def ch(c):
        if 0x01 <= c <= 0x1A:
            return chr(c + 0x40)
        if 0x20 <= c <= 0x29:
            return chr(c + 0x10)
        return signs.get(c, '#')
    return [''.join(ch(c) for c in codes[r * 40:r * 40 + 40]) for r in range(25)]


def prepare_sd(with_image=True):
    if os.path.isdir(SD):
        shutil.rmtree(SD)
    os.makedirs(os.path.join(SD, 'romwbw'))
    if with_image:
        shutil.copy(ROM, os.path.join(SD, 'romwbw', 'MZ800_std.rom'))


def start_loader(emu):
    exec_addr = emu.load_mzf(MZF)
    emu.set_pc(exec_addr)


def test_boot(memext):
    print('--- MemExt %s, image on the SD card' % memext)
    prepare_sd()
    sym = load_lst(run_hbios.LST)
    with Emu(memext=memext, unicard_sd=SD, fill='RANDOM') as emu:
        start_loader(emu)
        emu.run(20)
        screen = '\n'.join(text700(emu))
        check('ROMWBW LOADER FOR SHARP MZ-800' in screen, 'loader title on the MZ-700 screen')
        check(('MEMEXT: PEHU 512K' if memext == 'PEHU' else 'MEMEXT: LUFTNER 512K') in screen, 'MemExt type shown')
        lines = run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        check(any('Boot [H=Help]:' in l for l in lines), 'HBIOS boot loader prompt after loading')
        run_console.type_text(emu, 'z\r')
        lines = run_console.wait_for(emu, sym, 'A>')
        run_console.type_text(emu, 'dir\r')
        emu.run(150)                         # let the listing finish
        lines = screen_text(emu, sym)
        screen = '\n'.join(lines)
        check('COPY    .COM' in screen and 'DDT     .COM' in screen,
              'RAM disk filled from the image (DIR shows COPY.COM, DDT.COM)')
        check(lines[-1].startswith('A>') or any(l.rstrip() == 'A>' for l in lines[-3:]), 'DIR finished, A> prompt')
        print('\n'.join(l.rstrip() for l in lines[-12:]))


def test_stop(memext, with_image, expect, label):
    print('--- %s' % label)
    prepare_sd(with_image)
    with Emu(memext=memext, unicard_sd=SD) as emu:
        start_loader(emu)
        emu.run(30)
        screen = '\n'.join(text700(emu))
        check(expect in screen and 'STOPPED.' in screen, 'loader stops with "%s"' % expect)


if __name__ == '__main__':
    test_boot('PEHU')
    test_boot('LUFTNER')
    test_stop(None, True, 'ERROR: NO MEMEXT', 'no MemExt')
    test_stop('PEHU', False, 'NOT FOUND', 'no image file')
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
