"""Extended CPC DSK images of MZ-800 floppies (Lamac's CP/M and RomWBW formats), standard library only.

    python mzdev/tools/mzdsk.py new work/dsk/b720.dsk 720 [--lamac]
    python mzdev/tools/mzdsk.py toraw work/dsk/b720.dsk work/dsk/b720.img
    python mzdev/tools/mzdsk.py fromraw work/dsk/b720.dsk work/dsk/b720.img
    python mzdev/tools/mzdsk.py info work/dsk/b720.dsk

Formats: 720 = 80x2x9x512, 360 = 40x2x9x512 (sector IDs 1..9, interleave 1,6,2,7,3,8,4,9,5 as Lamac formats).
--lamac makes cylinder 0 / side 1 the MZ-800 IPL boot track (16 sectors of 256 B), as on Lamac's system disks.

The raw image is the CP/M view: logical track t = cylinder * 2 + side, sectors 1..9 in order, 4608 B per track.
A track that is not 9 x 512 (the boot track) is filled with E5h in the raw image and left alone by fromraw.
cpmtools then reads the raw image with the RomWBW disk definitions wbw_fd720 / wbw_fd360 (Tools/cpmtools/diskdefs).

The DSK holds the bytes as they are on the disk. The MZ-800 bus inverts them, the drivers (Lamac's BIOS and
RomWBW mzfd.asm) complement them again, so the data area of the DSK is what CP/M sees.
"""
import argparse
import struct
import sys

FORMATS = {720: (80, 2, 9), 360: (40, 2, 9)}
SKEW9 = [1, 6, 2, 7, 3, 8, 4, 9, 5]
SECTOR = 512


class Dsk:
    """tracks[(cylinder, side)] = list of sectors [c, h, r, n, st1, st2, data(bytearray)] in track order."""

    def __init__(self):
        self.cyls = 0
        self.sides = 0
        self.tracks = {}
        self.creator = b'mzdsk MZ800   '

    @classmethod
    def load(cls, path):
        d = open(path, 'rb').read()
        if not d.startswith(b'EXTENDED CPC DSK File'):
            raise ValueError('%s: not an Extended CPC DSK' % path)
        self = cls()
        self.creator = d[34:48]
        self.cyls, self.sides = d[0x30], d[0x31]
        table = [d[0x34 + i] * 256 for i in range(self.cyls * self.sides)]
        trust = 256 + sum(table) == len(d)      # the emulator is known to rewrite the size table wrongly
        off = 256
        for i in range(self.cyls * self.sides):
            if table[i] == 0:
                continue
            ti = d[off:off + 256]
            if not ti.startswith(b'Track-Info'):
                if trust:
                    raise ValueError('%s: bad Track-Info at %d' % (path, off))
                nxt = d.find(b'Track-Info' + bytes([13, 10]), off)    # damaged image: resync on the next track
                if nxt < 0:
                    break
                off = nxt
                ti = d[off:off + 256]
            ns = ti[0x15]
            size = table[i]
            if not trust:
                size = 256 + sum(struct.unpack('<H', ti[0x1E + 8 * k:0x20 + 8 * k])[0] or (128 << ti[0x1B + 8 * k])
                                 for k in range(ns))
                size = (size + 255) // 256 * 256
            pos = off + 256
            secs = []
            for k in range(ns):
                c, h, r, n, st1, st2, ln = struct.unpack('<BBBBBBH', ti[0x18 + 8 * k:0x20 + 8 * k])
                if ln == 0:
                    ln = 128 << n
                secs.append([c, h, r, n, st1, st2, bytearray(d[pos:pos + ln])])
                pos += ln
            key = (ti[0x10], ti[0x11])
            if key not in self.tracks:                  # a damaged image may repeat a track header
                self.tracks[key] = secs
            off += size
        return self

    @classmethod
    def new(cls, capacity, lamac=False):
        cyls, sides, spt = FORMATS[capacity]
        self = cls()
        self.cyls, self.sides = cyls, sides
        for c in range(cyls):
            for h in range(sides):
                if lamac and c == 0 and h == 1:
                    # MZ-800 IPL boot track: 16 x 256 B in order
                    self.tracks[(c, h)] = [[c, h, r, 1, 0, 0, bytearray([0xE5]) * 256] for r in range(1, 17)]
                else:
                    order = SKEW9 if spt == 9 else list(range(1, spt + 1))
                    self.tracks[(c, h)] = [[c, h, r, 2, 0, 0, bytearray([0xE5]) * SECTOR] for r in order]
        return self

    def save(self, path):
        header = bytearray(256)
        header[0:34] = b'EXTENDED CPC DSK File\r\nDisk-Info\r\n'
        header[34:48] = self.creator[:14].ljust(14)
        header[0x30], header[0x31] = self.cyls, self.sides
        body = bytearray()
        for i in range(self.cyls * self.sides):
            key = (i // self.sides, i % self.sides)
            secs = self.tracks.get(key)
            if not secs:
                continue
            ti = bytearray(256)
            ti[0:12] = b'Track-Info\r\n'
            ti[0x10], ti[0x11] = key
            ti[0x14] = secs[0][3]
            ti[0x15] = len(secs)
            ti[0x16] = 0x4E
            ti[0x17] = 0xE5
            data = bytearray()
            for k, (c, h, r, n, st1, st2, sd) in enumerate(secs):
                ti[0x18 + 8 * k:0x20 + 8 * k] = struct.pack('<BBBBBBH', c, h, r, n, st1, st2, len(sd))
                data += sd
            blk = ti + data
            if len(blk) % 256:
                blk += bytes(256 - len(blk) % 256)
            header[0x34 + i] = len(blk) // 256
            body += blk
        with open(path, 'wb') as f:
            f.write(header + body)

    def sector(self, c, h, r):
        for s in self.tracks.get((c, h), []):
            if s[2] == r:
                return s[6]
        return None

    def to_raw(self, spt=9):
        out = bytearray()
        for t in range(self.cyls * self.sides):
            c, h = t // self.sides, t % self.sides
            for r in range(1, spt + 1):
                s = self.sector(c, h, r)
                out += s if s is not None and len(s) == SECTOR else bytes([0xE5]) * SECTOR
        return bytes(out)

    def from_raw(self, raw, spt=9):
        size = spt * SECTOR
        for t in range(len(raw) // size):
            c, h = t // self.sides, t % self.sides
            for r in range(1, spt + 1):
                s = self.sector(c, h, r)
                if s is not None and len(s) == SECTOR:
                    pos = t * size + (r - 1) * SECTOR
                    s[:] = raw[pos:pos + SECTOR]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('new')
    p.add_argument('dsk')
    p.add_argument('capacity', type=int, choices=sorted(FORMATS))
    p.add_argument('--lamac', action='store_true', help='IPL boot track at cylinder 0 / side 1')
    for name in ('toraw', 'fromraw'):
        p = sub.add_parser(name)
        p.add_argument('dsk')
        p.add_argument('img')
    p = sub.add_parser('info')
    p.add_argument('dsk')
    a = ap.parse_args()
    if a.cmd == 'new':
        Dsk.new(a.capacity, a.lamac).save(a.dsk)
    elif a.cmd == 'toraw':
        with open(a.img, 'wb') as f:
            f.write(Dsk.load(a.dsk).to_raw())
    elif a.cmd == 'fromraw':
        d = Dsk.load(a.dsk)
        d.from_raw(open(a.img, 'rb').read())
        d.save(a.dsk)
    elif a.cmd == 'info':
        d = Dsk.load(a.dsk)
        print('%s: %d cylinders, %d sides' % (a.dsk, d.cyls, d.sides))
        for key in sorted(d.tracks)[:4]:
            print('  C%d H%d:' % key, ' '.join('%d/%d' % (s[2], len(s[6])) for s in d.tracks[key]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
