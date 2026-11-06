"""Extended CPC DSK images of MZ-800 floppies (Lamac's CP/M and RomWBW formats), standard library only.

    python mzdev/tools/mzdsk.py new work/dsk/b720.dsk 720 [--lamac]
    python mzdev/tools/mzdsk.py toraw work/dsk/b720.dsk work/dsk/b720.img
    python mzdev/tools/mzdsk.py fromraw work/dsk/b720.dsk work/dsk/b720.img
    python mzdev/tools/mzdsk.py info work/dsk/b720.dsk
    python mzdev/tools/mzdsk.py mkboot work/dsk/boot.dsk 720 [--ipl Binary/mz800-ipl.bin] [--sys zsys_wbw.sys]
                                [--image Binary/MZ800_std.rom] [--file path[=NAME.EXT] ...]

Formats: 720 = 80x2x9x512, 360 = 40x2x9x512 (sector IDs 1..9, interleave 1,6,2,7,3,8,4,9,5 as Lamac formats).
--lamac makes cylinder 0 / side 1 the MZ-800 IPL boot track (16 sectors of 256 B), as on Lamac's system disks.

mkboot makes a RomWBW boot disk in the MZ layout (Lamac's): the IPL loader (Source/MZ800/mzipl.asm) on the boot
track, the RomWBW image as file ROMWBW.ROM, optionally a CP/M system (.sys from SYSCOPY, 27 sectors) in the
reserved tracks for the boot loader's disk boot, and more files. The reserved tracks of the MZ layout are mapped as
mzfd.asm maps them: logical tracks 0, 1, 2 are cylinder 0 side 0, cylinder 1 side 0, cylinder 1 side 1, logical
track 3 is the boot track (cylinder 0 side 1).

The raw image is the CP/M view: logical track t = cylinder * 2 + side, sectors 1..9 in order, 4608 B per track.
A track that is not 9 x 512 (the boot track) is filled with E5h in the raw image and left alone by fromraw.
cpmtools then reads the raw image with the RomWBW disk definitions wbw_fd720 / wbw_fd360 (Tools/cpmtools/diskdefs).

The DSK holds the bytes as they are on the disk. The MZ-800 bus inverts them, the drivers (Lamac's BIOS and
RomWBW mzfd.asm) complement them again, so the data area of the DSK is what CP/M sees.
"""
import argparse
import os
import struct
import subprocess
import sys
import tempfile

FORMATS = {720: (80, 2, 9), 360: (40, 2, 9)}
SKEW9 = [1, 6, 2, 7, 3, 8, 4, 9, 5]
SECTOR = 512
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
CPMTOOLS = os.path.join(ROOT, 'Tools', 'cpmtools')
RESERVED = [(0, 0), (1, 0), (1, 1)]      # logical reserved tracks 0-2 of the MZ layout (track 3 is the boot track)
IPL_PARAMS = 256 + 2                     # "RWB", format, double step, name (after the jump at $1200)


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


def cpm_name(name):
    """'romwbw.rom' -> b'ROMWBW  ROM' (11 bytes as in a directory entry)."""
    base, _, ext = name.upper().partition('.')
    return (base[:8].ljust(8) + ext[:3].ljust(3)).encode('ascii')


def put_files(dsk, capacity, files):
    """Copy host files into the CP/M data area with cpmtools. files: list of (host path, CP/M name)."""
    fmt = 'wbw_fd%d' % capacity
    fd, img = tempfile.mkstemp(suffix='.img')
    os.close(fd)
    try:
        with open(img, 'wb') as f:
            f.write(dsk.to_raw())
        for path, name in files:
            r = subprocess.run([os.path.join(CPMTOOLS, 'cpmcp.exe'), '-f', fmt, img, os.path.abspath(path),
                                '0:' + name.lower()], cwd=CPMTOOLS, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('cpmcp %s: %s' % (name, r.stdout + r.stderr))
        dsk.from_raw(open(img, 'rb').read())
    finally:
        os.remove(img)


def mkboot(capacity, ipl, image=None, image_name='ROMWBW.ROM', sysimg=None, files=()):
    """RomWBW boot disk in the MZ layout (see the module documentation). Returns the Dsk."""
    d = Dsk.new(capacity, lamac=True)
    ipl = bytearray(ipl)
    if len(ipl) != 4096 or ipl[0:7] != b'\x03IPLPRO' or ipl[IPL_PARAMS:IPL_PARAMS + 3] != b'RWB':
        raise ValueError('not an MZ-800 RomWBW IPL image')
    ipl[IPL_PARAMS + 3] = 0 if capacity == 720 else 1          # format
    ipl[IPL_PARAMS + 4] = 0                                       # no double stepping
    ipl[IPL_PARAMS + 5:IPL_PARAMS + 16] = cpm_name(image_name)
    for r in range(1, 17):                                        # stored complemented
        d.sector(0, 1, r)[:] = bytes(255 - b for b in ipl[(r - 1) * 256:r * 256])
    if sysimg is not None:
        if len(sysimg) > 27 * SECTOR:
            raise ValueError('system image too big for the reserved tracks (%d B)' % len(sysimg))
        sysimg = sysimg.ljust(27 * SECTOR, b'\xE5')
        for i in range(27):
            c, h = RESERVED[i // 9]
            d.sector(c, h, i % 9 + 1)[:] = sysimg[i * SECTOR:(i + 1) * SECTOR]
    todo = list(files)
    if image is not None:
        todo.insert(0, (image, image_name))
    if todo:
        put_files(d, capacity, todo)
    return d


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
    p = sub.add_parser('mkboot')
    p.add_argument('dsk')
    p.add_argument('capacity', type=int, choices=sorted(FORMATS))
    p.add_argument('--ipl', default=os.path.join(ROOT, 'Binary', 'mz800-ipl.bin'))
    p.add_argument('--image', default=os.path.join(ROOT, 'Binary', 'MZ800_std.rom'),
                   help='RomWBW image, stored as ROMWBW.ROM ("" for none)')
    p.add_argument('--sys', help='CP/M system for the reserved tracks (e.g. Binary/ZSDOS/zsys_wbw.sys)')
    p.add_argument('--file', action='append', default=[], help='host file [=CP/M name], repeatable')
    a = ap.parse_args()
    if a.cmd == 'mkboot':
        files = []
        for spec in a.file:
            path, _, name = spec.partition('=')
            files.append((path, name or os.path.basename(path)))
        sysimg = open(a.sys, 'rb').read() if a.sys else None
        d = mkboot(a.capacity, open(a.ipl, 'rb').read(), a.image or None, sysimg=sysimg, files=files)
        d.save(a.dsk)
        print('%s: %dK MZ boot disk, %d files%s' % (a.dsk, a.capacity, len(files) + (1 if a.image else 0),
                                                   ', system in the reserved tracks' if sysimg else ''))
    elif a.cmd == 'new':
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
