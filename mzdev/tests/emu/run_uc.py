"""Stage 7: UC.COM, files of the Unicard SD card from CP/M.

The system starts through the Unicard loader (SD root mzdev/work/sd), UC.COM is on a floppy in drive 0, a test
file of 1000 bytes in the SD root:
- UC DIR lists the SD root (the loader MZF, the romwbw folder);
- UC GET copies the test file to the floppy (1000 bytes, rounded up to 1024 with ^Z);
- UC PUT copies it back under another name, the host compares it;
- UC CD changes into the romwbw folder.

    python mzdev/tests/emu/run_uc.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from mzemu import Emu, ROOT, WORK  # noqa: E402
from tasmlst import load_lst  # noqa: E402
from mzdsk import Dsk, put_files  # noqa: E402
import run_hbios  # noqa: E402
import run_console  # noqa: E402
import run_loader  # noqa: E402

FD0 = os.path.join(WORK, 'dsk', 'uc.dsk')

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def main():
    run_loader.prepare_sd()
    data = bytes((i * 7 + 3) & 0xFF for i in range(1000))
    with open(os.path.join(run_loader.SD, 'test.bin'), 'wb') as f:
        f.write(data)
    d = Dsk.new(720)
    put_files(d, 720, [(os.path.join(ROOT, 'Binary', 'Apps', 'uc.com'), 'UC.COM')], lamac=False)
    d.save(FD0)
    sym = load_lst(run_hbios.LST)
    with Emu(memext='PEHU', unicard_sd=run_loader.SD, fdd={0: FD0}, fdd_storage={0: 'cached'}) as emu:
        run_loader.start_loader(emu)
        run_console.wait_for(emu, sym, 'Boot [H=Help]:', 1500, 20)
        run_console.type_text(emu, 'z\r')
        run_console.wait_for(emu, sym, 'A>')
        lines = run_console.run_cmd(emu, sym, 'b:uc dir')
        text = '\n'.join(l.rstrip() for l in lines if l.strip())
        print(text[-600:])
        check('MZ800-LDR.MZF' in text.upper() and 'ROMWBW/' in text.upper() and 'TEST.BIN' in text.upper(),
              'UC DIR lists the SD root')
        lines = run_console.run_cmd(emu, sym, 'b:uc get test.bin b:test.bin', 1500)
        check(any('done.' in l for l in lines), 'UC GET copies the SD file to the floppy')
        lines = run_console.run_cmd(emu, sym, 'b:uc put b:test.bin back.bin', 1500)
        check(any('done.' in l for l in lines), 'UC PUT copies it back')
        lines = run_console.run_cmd(emu, sym, 'b:uc cd romwbw')
        print('\n'.join(l.rstrip() for l in lines if l.strip())[-300:])
        check(any('MZ800_STD.ROM' in l.upper() for l in lines), 'UC CD changes into the romwbw folder')
    back = open(os.path.join(run_loader.SD, 'back.bin'), 'rb').read() \
        if os.path.exists(os.path.join(run_loader.SD, 'back.bin')) else b''
    check(back == data + b'\x1a' * 24, 'the round trip keeps the data (%d bytes, 1000 + ^Z to 1024)' % len(back))


if __name__ == '__main__':
    main()
    print('FAILED: %d' % len(failures) if failures else 'ALL OK')
    sys.exit(1 if failures else 0)
