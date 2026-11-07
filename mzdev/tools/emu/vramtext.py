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
    glyphs = [bytes(_mirror(b) for b in raw[ch * 8:ch * 8 + 8]) for ch in range(256)]
    # plain glyphs first: a blank cell with the cursor looks like '_', the cursor cell is undone in decode()
    for cursor in (False, True):
        for ch, g in enumerate(glyphs):
            variant = g[:7] + bytes([g[7] ^ 0xFF]) if cursor else g
            table.setdefault(variant, chr(ch))
            table.setdefault(bytes(b ^ 0xFF for b in variant), chr(ch))   # reverse video
    return table


_TABLE = None


def decode(plane1, plane2, sof_units, cursor=None):
    """25 strings of 80 characters from the raw VRAM planes I and II (8000 bytes each). cursor: (row, col) of a
    drawn cursor (inverted bottom raster line), undone before the cell is matched."""
    global _TABLE
    if _TABLE is None:
        _TABLE = _glyph_table()
    sofb = sof_units * 8
    bitmap = bytearray(16000)
    for a in range(16000):
        phys = ((a >> 1) + sofb) % 8000
        bitmap[a] = (plane2 if a & 1 else plane1)[phys]
    if cursor and 0 <= cursor[0] < ROWS and 0 <= cursor[1] < COLS:
        bitmap[cursor[0] * 640 + cursor[1] + 7 * 80] ^= 0xFF
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
    cursor = None
    if 'MZV_POS' in sym and emu.memext_read(sym['MZV_CURVIS'], 1)[0]:
        pos = emu.memext_read(sym['MZV_POS'], 2)                # E = column, D = row
        cursor = (pos[1], pos[0])
    return decode(emu.vram_plane(0, 8000), emu.vram_plane(1, 8000), sof[0] | sof[1] << 8, cursor)
