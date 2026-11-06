"""Label addresses from a TASM listing (RomWBW builds with -g3 and a .lst, no symbol file).

TASM 3.2 listing lines: 'NNNN[+...]  AAAA[~] BB BB ...' with the source text from column 24. A '~' after the
address marks a line in a false conditional block (not assembled); those are skipped. Only labels at the start
of the source text are collected, equates are not (their address column is not their value). The first
definition wins.

    from tasmlst import load_lst
    sym = load_lst('Source/HBIOS/hbios_rom.lst')
    sym['HB_START']
"""
import re

HEAD = re.compile(r'^\d{4}\+*\s+([0-9A-F]{4})([ ~])')
LABEL = re.compile(r'([A-Za-z_][A-Za-z0-9_]*):?(?=[\s;]|$)')


def load_lst(path):
    out = {}
    for line in open(path, encoding='latin-1'):
        line = line.rstrip('\r\n')
        m = HEAD.match(line)
        if not m or m.group(2) == '~' or len(line) <= 24:
            continue
        src = line[24:]
        if src[0] in ' \t;#.':
            continue
        lm = LABEL.match(src)
        if not lm:
            continue
        if src[lm.end():].lstrip().upper().startswith(('.EQU', '.SET')):
            continue
        out.setdefault(lm.group(1), int(m.group(1), 16))
    return out


if __name__ == '__main__':
    import sys
    syms = load_lst(sys.argv[1])
    for name in sys.argv[2:]:
        print('%-16s %s' % (name, ('%04X' % syms[name]) if name in syms else '?'))
