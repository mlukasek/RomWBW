"""Screen text of the MZ-800 RomWBW console (mzv.asm) decoded from VRAM by glyph matching, for test assertions.

The console draws the 8x8 RomWBW font (Source/Fonts/font8x8u.bin, mirrored: bit 0 = leftmost pixel) into the
640x200 monochrome bitmap. In 640 mode CPU address A (0..15999 from $8000) is VRAM plane I (A even) or plane II
(A odd) at physical byte A >> 1; the hardware scroll adds SOF (driver units * 8 bytes) modulo 8000 (scroll area =
whole screen, as set by the driver). A text cell (row r, column c) is the 8 bytes at A = r*640 + c + line*80.

Cells are matched exactly, also with the cursor (bottom line inverted) and in reverse video; anything else is '?'.

    from vramtext import screen_text
    lines = screen_text(emu, sym)          # 25 strings of 80 characters
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
FONT = os.path.join(ROOT, 'Source', 'Fonts', 'font8x8u.bin')
ROWS, COLS = 25, 80


def _mirror(b):
    return int('{:08b}'.format(b)[::-1], 2)


def _glyph_table():
    raw = open(FONT, 'rb').read()
    table = {}
    for ch in range(256):
        g = bytes(_mirror(b) for b in raw[ch * 8:ch * 8 + 8])
        for variant in (g, g[:7] + bytes([g[7] ^ 0xFF])):          # plain, with cursor
            table.setdefault(variant, chr(ch))
            table.setdefault(bytes(b ^ 0xFF for b in variant), chr(ch))   # reverse video
    return table


_TABLE = None


def decode(plane1, plane2, sof_units):
    """25 strings of 80 characters from the raw VRAM planes I and II (8000 bytes each)."""
    global _TABLE
    if _TABLE is None:
        _TABLE = _glyph_table()
    sofb = sof_units * 8
    bitmap = bytearray(16000)
    for a in range(16000):
        phys = ((a >> 1) + sofb) % 8000
        bitmap[a] = (plane2 if a & 1 else plane1)[phys]
    lines = []
    for r in range(ROWS):
        chars = []
        for c in range(COLS):
            cell = bytes(bitmap[r * 640 + c + i * 80] for i in range(8))
            ch = _TABLE.get(cell, '?')
            chars.append(ch if 32 <= ord(ch) < 127 else ('?' if ch != '\0' else ' '))
        lines.append(''.join(chars))
    return lines


def screen_text(emu, sym):
    """Decode the live screen: VRAM planes from the emulator, SOF from the driver variable MZV_SOF (HBIOS bank)."""
    sof = emu.memext_read(sym['MZV_SOF'], 2)
    return decode(emu.vram_plane(0, 8000), emu.vram_plane(1, 8000), sof[0] | sof[1] << 8)
