"""Stage 1 bring-up: load the ROM-less HBIOS image (Binary/MZ800_std.upd) straight into MemExt RAM (RomWBW banks
$80-$83 = MemExt offsets 0-128K for both board types), switch the MZ-800 ROM out, start it at 0 and check:
- the MemExt type detected by HBIOS (MZ_MXTYPE in the HBIOS bank) and the patched proxy bank select;
- HBIOS finishes its init and the boot loader (romldr, bank BID_USR $8E) runs and polls the console;
- without MemExt, HBIOS stops at MZ_NOMX (red border, HALT).

    python mzdev/tests/emu/run_hbios.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools', 'emu'))
from mzemu import Emu, ROOT  # noqa: E402
from tasmlst import load_lst  # noqa: E402

UPD = os.path.join(ROOT, 'Binary', 'MZ800_std.upd')
LST = os.path.join(ROOT, 'Source', 'HBIOS', 'hbios_rom.lst')
LDR_LST = os.path.join(ROOT, 'Source', 'HBIOS', 'romldr.lst')
BID_BIOS, BID_USR = 0x80, 0x8E
HB_CURBNK = 0xFFE0

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def boot(emu, image):
    """Reset, let the IPL settle, put the image into MemExt, switch ROM/CG-ROM/VRAM out and jump to 0."""
    emu.reset()
    emu.run(10)
    emu.memext_write(0, image)
    emu.io_out(0xE0, 0)          # RAM at 0000-1FFF
    emu.io_out(0xE1, 0)          # RAM at E000-FFFF
    emu.io_in(0xE1)              # CG-ROM and VRAM out
    emu.set_pc(0)


def bios_byte(emu, addr):
    """Byte of the HBIOS bank (BID_BIOS = MemExt offset 0) regardless of the current mapping."""
    return emu.memext_read((BID_BIOS & 0x0F) * 0x8000 + addr, 1)[0]


def test_type(memext, mxtype, x8, step):
    print('--- MemExt %s' % memext)
    sym = load_lst(LST)
    image = open(UPD, 'rb').read()
    with Emu(memext=memext) as emu:
        boot(emu, image)
        emu.run(100)
        check(bios_byte(emu, sym['MZ_MXTYPE']) == mxtype, 'HBIOS detected MemExt type %d' % mxtype)
        check(emu.mem(0xFE00, 2) == b'W\xa8', 'proxy installed at FE00 (ident W~W)')
        check(emu.byte(sym['HBX_MZX8']) == x8 and emu.word(sym['HBX_MZSTEP'] + 1) == step,
              'proxy bank select patched: %02X / %04X' % (x8, step))
        ldr = load_lst(LDR_LST)
        lo, hi = min(ldr.values()), max(ldr.values())
        banks = set()
        user_code = False
        for _ in range(30):
            emu.call('run', {'frames': 1})
            bank = emu.byte(HB_CURBNK)
            banks.add(bank)
            user_code |= bank == BID_USR and lo <= emu.regs()['PC'] <= hi
        check(banks <= {BID_BIOS, BID_USR} and BID_USR in banks,
              'boot loader runs in bank %02X and calls HBIOS (banks seen: %s)'
              % (BID_USR, ' '.join('%02X' % b for b in sorted(banks))))
        check(user_code, 'CPU seen in romldr code (%04X-%04X) in bank %02X' % (lo, hi, BID_USR))


def test_none():
    print('--- no MemExt')
    sym = load_lst(LST)
    image = open(UPD, 'rb').read()
    with Emu(memext=None) as emu:
        emu.reset()
        emu.run(10)
        emu.io_out(0xE0, 0)
        emu.io_out(0xE1, 0)
        emu.io_in(0xE1)
        emu.poke(0, image[:0x8000])          # the HBIOS bank into plain RAM
        emu.set_pc(0)
        emu.run(20)
        pc = emu.regs()['PC']
        check(sym['MZ_NOMX'] <= pc <= sym['MZ_MXEND'], 'HBIOS stops in MZ_NOMX (PC=%04X)' % pc)


test_type('PEHU', 0, 0x00, 0x2004)
test_type('LUFTNER', 1, 0x07, 0x1008)
test_none()
print('FAILED: %d' % len(failures) if failures else 'ALL OK')
sys.exit(1 if failures else 0)
