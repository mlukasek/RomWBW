"""Stage 0 harness check: the emulator starts with our ini, all 512 KB of MemExt RAM can be written and read
by the harness, and the E7h page mapping behaves as the RomWBW memory manager will assume:
- PEHU: data = 8 KB bank, a write to an odd page goes to the even/odd page pair;
- Luftner: data = 4 KB bank, every page on its own;
- no MemExt: E7h ignored.

    python mzdev/tests/emu/run_memext.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools', 'emu'))
from mzemu import Emu  # noqa: E402

failures = []


def check(cond, msg):
    print(('ok    ' if cond else 'FAIL  ') + msg)
    if not cond:
        failures.append(msg)


def marker(bank):
    return bytes([0xA5, bank & 0xFF, 0x5A, (bank >> 8) & 0xFF]) * 4


def test_type(memext, bank_size, pair):
    print('--- MemExt %s' % memext)
    with Emu(memext=memext) as emu:
        emu.run(5)
        check(('memext_ram', 0) in emu.regions(), 'memext_ram region present')
        banks = 512 * 1024 // bank_size
        for b in range(banks):
            emu.memext_write(b * bank_size, marker(b))
        check(all(emu.memext_read(b * bank_size, 16) == marker(b) for b in range(banks)),
              'all 512 KB reachable: markers read back from %d banks of %d KB' % (banks, bank_size // 1024))
        # bank 20h into page 4 (4000h) through port E7h, A12-A15 = page
        emu.io_out(0x40E7, 0x20)
        check(emu.mem(0x4000, 16) == marker(0x20), 'OUT (40E7h),20h maps bank 20h at 4000h')
        # write the odd page 5 only: PEHU aligns it to the pair 4-5 (4000h follows), Luftner does not
        emu.io_out(0x50E7, 0x22)
        at4000 = emu.mem(0x4000, 16)
        if pair:
            check(at4000 == marker(0x22), 'PEHU: OUT to page 5 remaps the pair, 4000h shows bank 22h')
        else:
            check(at4000 == marker(0x20), 'Luftner: OUT to page 5 leaves 4000h at bank 20h')
            check(emu.mem(0x5000, 16) == marker(0x22), 'Luftner: 5000h shows bank 22h')
        # the highest bank (top of the common area later)
        top = banks - 1
        emu.io_out(0x40E7, top)
        check(emu.mem(0x4000, 16) == marker(top), 'highest bank %02Xh mapped at 4000h' % top)
        # a CPU write lands in the mapped bank
        emu.io_out(0x40E7, 0x21)
        emu.poke(0x4010, b'MZ-RomWBW')
        check(emu.memext_read(0x21 * bank_size + 0x10, 9) == b'MZ-RomWBW', 'CPU write lands in bank 21h')


def test_none():
    print('--- no MemExt')
    with Emu(memext=None) as emu:
        emu.run(5)
        check(('memext_ram', 0) not in emu.regions(), 'no memext_ram region')
        emu.poke(0x4000, b'\x11\x22\x33\x44')
        emu.io_out(0x40E7, 0x20)
        check(emu.mem(0x4000, 4) == b'\x11\x22\x33\x44', 'OUT (40E7h) has no effect')


test_type('PEHU', 8192, True)
test_type('LUFTNER', 4096, False)
test_none()
print('FAILED: %d' % len(failures) if failures else 'ALL OK')
sys.exit(1 if failures else 0)
