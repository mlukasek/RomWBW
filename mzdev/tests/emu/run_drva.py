"""Drive A: of the MZ-800 (the RAM disk in MemExt, loaded from the .rom image, Source/MZ800/Build.cmd).

The system starts through the Unicard loader (SD root mzdev/work/sd) and boots ZSDOS. Checks:
- DIR A: lists the MZ-800 utilities (UC, MZSYS, MZFMT) and WDATE, but not FDU, FLASH and RTC;
- WDATE (date and time through HBIOS) shows the date of the host (the emulated Unicard RTC is the host clock);
- UC runs from A: (UC DIR lists the SD root).

    python mzdev/tests/emu/run_drva.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
from mzemu import Emu  # noqa: E402
from tasmlst import load_lst  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def main():
    run_loader.prepare_sd()
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', unicard_sd=run_loader.SD) as emu:
        run_loader.start_loader(emu)
        run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        run_console.type_text(emu, 'z\r')
        run_console.wait_for(emu, sym, 'A>')
        lines = run_console.run_cmd(emu, sym, 'dir a:')
        text = ' '.join(l.rstrip() for l in lines).upper()
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-900:])
        for name in ('UC', 'MZSYS', 'MZFMT', 'WDATE'):
            check(' %s ' % name in text.replace(':', ' ').replace('.', ' '), '%s.COM on A:' % name)
        for name in ('FDU', 'FLASH', 'RTC'):
            check(' %s ' % name not in text.replace(':', ' ').replace('.', ' '), '%s.COM not on A:' % name)
        lines = run_console.run_cmd(emu, sym, 'wdate')
        out = [l.rstrip() for l in lines if l.strip()]
        print('\n'.join(out[-3:]))
        today = time.localtime()
        line = out[-2] if len(out) >= 2 else ''
        check(time.strftime('%B', today) in line and str(today.tm_year) in line and
              (' %02d ' % today.tm_mday) in line, 'WDATE shows the date of the host: %s' % line.strip())
        lines = run_console.run_cmd(emu, sym, 'uc dir')
        text = '\n'.join(l.rstrip() for l in lines if l.strip())
        check('MZ800-LDR.MZF' in text.upper() and 'ROMWBW/' in text.upper(), 'UC DIR from A: lists the SD root')


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
