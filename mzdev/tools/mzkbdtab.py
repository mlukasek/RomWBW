"""Generate the key translation tables of Source/HBIOS/mzkbd.asm (SHARP MZ-800 keyboard matrix -> RomWBW codes).

Matrix positions from mz800emu docs/agent/mz800_keyboard.md (verified against the MZ-800 ROM): column = value
written to 8255 PA0-3 (0-9), bit = bit of the byte read from PB (active low). Table index = column * 8 + bit.

Codes: plain ASCII, RomWBW special keys ($E0 F1 ... $F9 RIGHT, see ansi.asm ANSI_KDISP), 0 = no key (modifiers and
unused positions are handled by the driver itself).

    python mzdev/tools/mzkbdtab.py      # prints the .DB lines
"""

F1, INS, DELF, HOME, UP, DOWN, LEFT, RIGHT = 0xE0, 0xF0, 0xF1, 0xF2, 0xF6, 0xF7, 0xF8, 0xF9
BS, TAB, CR, ESC = 0x08, 0x09, 0x0D, 0x1B

# (column, bit): (normal, shifted)
KEYS = {
    (0, 0): (CR, CR),
    (0, 1): (':', '*'),
    (0, 2): (';', '+'),
    (0, 3): (TAB, TAB),
    # (0, 4) ALPHA = caps lock toggle, (0, 6) GRAPH = reserved (line recall), (0, 7) BLANK = unused
    (0, 5): ('`', '`'),           # DOWN_ARROW key (Sharp down arrow / pound sign)
    (1, 3): (']', '|'),
    (1, 4): ('[', '{'),
    (1, 5): ('@', '`'),
    (1, 6): ('z', 'Z'),
    (1, 7): ('y', 'Y'),
    (2, 0): ('x', 'X'), (2, 1): ('w', 'W'), (2, 2): ('v', 'V'), (2, 3): ('u', 'U'),
    (2, 4): ('t', 'T'), (2, 5): ('s', 'S'), (2, 6): ('r', 'R'), (2, 7): ('q', 'Q'),
    (3, 0): ('p', 'P'), (3, 1): ('o', 'O'), (3, 2): ('n', 'N'), (3, 3): ('m', 'M'),
    (3, 4): ('l', 'L'), (3, 5): ('k', 'K'), (3, 6): ('j', 'J'), (3, 7): ('i', 'I'),
    (4, 0): ('h', 'H'), (4, 1): ('g', 'G'), (4, 2): ('f', 'F'), (4, 3): ('e', 'E'),
    (4, 4): ('d', 'D'), (4, 5): ('c', 'C'), (4, 6): ('b', 'B'), (4, 7): ('a', 'A'),
    (5, 0): ('8', '('), (5, 1): ('7', "'"), (5, 2): ('6', '&'), (5, 3): ('5', '%'),
    (5, 4): ('4', '$'), (5, 5): ('3', '#'), (5, 6): ('2', '"'), (5, 7): ('1', '!'),
    (6, 0): ('.', '>'),
    (6, 1): (',', '<'),
    (6, 2): ('9', ')'),
    (6, 3): ('0', '0'),           # Sharp: SHIFT+0 = pi
    (6, 4): (' ', ' '),
    (6, 5): ('-', '='),
    (6, 6): ('^', '~'),           # UP_ARROW key
    (6, 7): ('\\', '}'),
    (7, 0): ('/', '_'),           # Sharp: SHIFT+/ = left arrow = ASCII $5F
    (7, 1): ('?', '?'),           # Sharp: SHIFT+? = right arrow
    (7, 2): (LEFT, LEFT),
    (7, 3): (RIGHT, RIGHT),
    (7, 4): (DOWN, DOWN),
    (7, 5): (UP, UP),
    (7, 6): (BS, HOME),           # DEL: backspace, SHIFT = HOME (as in the Sharp monitor)
    (7, 7): (INS, DELF),          # INST: insert, SHIFT = delete (forward)
    # (8, 0) SHIFT, (8, 6) CTRL
    (8, 7): (ESC, ESC),
    (9, 7): (F1, F1 + 5), (9, 6): (F1 + 1, F1 + 6), (9, 5): (F1 + 2, F1 + 7),
    (9, 4): (F1 + 3, F1 + 8), (9, 3): (F1 + 4, F1 + 9),
}


def code(v):
    return ord(v) if isinstance(v, str) else v


def table(which):
    out = []
    for col in range(10):
        row = [code(KEYS[(col, bit)][which]) if (col, bit) in KEYS else 0 for bit in range(8)]
        out.append('\t.DB\t%s\t\t; COLUMN %d, BITS 0-7' % (', '.join('$%02X' % v for v in row), col))
    return '\n'.join(out)


if __name__ == '__main__':
    print('MZK_MAPNORM:\t\t\t\t; NORMAL')
    print(table(0))
    print('MZK_MAPSHFT:\t\t\t\t; WITH SHIFT')
    print(table(1))
