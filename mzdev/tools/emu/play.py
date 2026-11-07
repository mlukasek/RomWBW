"""RomWBW for the MZ-800 in the emulator window, for trying things by hand (standard library only).

    python mzdev/tools/emu/play.py [unicard|floppy|hd|cpm3] [--fd0 NAME] [--fd1 NAME] [--luftner] [--fresh]
                                   [--new-ramdisk] [--autoboot]

Prepares mzdev/work/play (once, --fresh makes it again from the current Binary/, --new-ramdisk only the RAM
disk) and starts mz800emu with a
window and its own ini (mzdev/work/play/mz800emu.ini, the emulator's own ini stays untouched):

- MemExt 512K (PEHU, --luftner for Luftner), the floppy controller with the HD modification;
- Unicard with the SD card mzdev/work/play/sd: mz800-ldr.mzf, romwbw/MZ800_std.rom, uc.com and friends;
- the Unicard RAM disk (the MZ-1R18 SRAM of the emulator on the same ports): 16 MB, hd1k_cpm3 + hd1k_zpm3, so
  UCRD0:0 is CP/M 3 and UCRD0:1 ZPM3 (boot loader: 3 and 3.1). Lamac's CP/M uses it as its RAM disk E: and
  formats it when it boots (the first 4K: the boot area of slice 0), --new-ramdisk makes it again;
- floppy images in mzdev/work/play/dsk (all copies, writes are kept):
    boot720.dsk   RomWBW boot disk 720K (IPL loader, ROMWBW.ROM = the full .rom, ZSDOS in the reserved tracks,
                  MZSYS, MZFMT, UC, ZSYS.SYS)
    boot144.dsk   the same as a 1.44M HD disk (Lamac's HD format)
    cpm3_144.dsk  1.44M boot disk with CP/M 3 in the reserved tracks and the CP/M 3 files (boot loader: 1)
    lamac_prg.dsk Lamac's CP/M 4.1 program disk (720K), lamac_sys.dsk his system disk
    martin144.dsk Lamac's 1.44M disk
    blank720.dsk, blank144.dsk  empty disks in Lamac's format (MZ layout)

Unicard: the runtime of the emulator (unicard/) is put on the SD card, so Q + reset boots the QuickDisk of the
Unicard and starts the Unicard Manager (mz800-ldr.mzf is in the root of the SD card), with --autoboot the RomWBW
loader directly. C + reset loads from the tape, M + reset enters the monitor.

Start modes:
    unicard  the Unicard loader runs (--run-mzf, only at the start of the emulator). Drive 0 holds
             unicard0.dsk, made empty again on every start, so a reset ends in the menu of the MZ-800 ROM (C loads
             an MZF from the tape: with the CMT hack of the emulator choose mzdev/work/play/sd/mz800-ldr.mzf);
             drive 1 holds lamac_prg.dsk
    floppy   power on with boot720.dsk in drive 0: the MZ-800 ROM boots RomWBW from it
    hd       the same with boot144.dsk
    cpm3     the same with cpm3_144.dsk (then 1 at the boot loader: CP/M 3 from the floppy)
--fd0 / --fd1 NAME put mzdev/work/play/dsk/NAME into drive 0 / 1 (drive 1: blank720.dsk by default, in the
unicard mode lamac_prg.dsk).

Keys of the MZ-800 on the PC keyboard: BLANK = ` (left of 1), ALPHA = \\, GRAPH = Caps Lock, INST = Insert,
DEL = Backspace or Delete, ESC (BREAK) = Esc or End, CTRL = left Ctrl, F1-F5 = F1-F5.
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from mzemu import EMU_DIR, ROOT, WORK, emu_overrides, make_ini  # noqa: E402

from mzdsk import Dsk, mkboot, image_def  # noqa: E402

PLAY = os.path.join(WORK, 'play')
SD = os.path.join(PLAY, 'sd')
DSK = os.path.join(PLAY, 'dsk')
RAMDISK = os.path.join(PLAY, 'ucrd16.img')
BIN = os.path.join(ROOT, 'Binary')
SIBLING = os.path.dirname(ROOT)
LAMAC_BOOT = ('lamac_prg.dsk', 'lamac_sys.dsk', 'martin144.dsk')   # Lamac's CP/M boots from these
UNICARD0 = 'unicard0.dsk'       # drive 0 of the unicard mode, made empty again on every start


def unicard_runtime(autoboot):
    """The Unicard runtime of the emulator on our SD card (unicard/: mgr800.mzf = Unicard Manager, mzfloader.mzq =
    the QuickDisk loader that Q + reset boots, mzfloader.cfg = the MZF it starts). autoboot: our loader instead of
    the Manager, as /unicard/mzfloader.cfg does on a real Unicard."""
    dst = os.path.join(SD, 'unicard')
    if not os.path.isdir(dst):
        shutil.copytree(os.path.join(EMU_DIR, 'SD-mz800', 'unicard'), dst)
    target = '/mz800-ldr.mzf' if autoboot else '/unicard/mgr800.mzf'
    with open(os.path.join(dst, 'mzfloader.cfg'), 'wb') as f:
        f.write(target.encode('ascii') + bytes([13]))     # CR terminated
    return target


def prepare(fresh, new_ramdisk=False):
    if fresh and os.path.isdir(PLAY):
        for name in ('sd', 'dsk'):
            shutil.rmtree(os.path.join(PLAY, name), ignore_errors=True)
    if (fresh or new_ramdisk) and os.path.exists(RAMDISK):
        os.remove(RAMDISK)
    os.makedirs(os.path.join(SD, 'romwbw'), exist_ok=True)
    os.makedirs(DSK, exist_ok=True)
    # SD card: the loader, the image, the utilities
    shutil.copy(os.path.join(BIN, 'mz800-ldr.mzf'), SD)
    shutil.copy(os.path.join(BIN, 'MZ800_std.rom'), os.path.join(SD, 'romwbw'))
    for name in ('uc.com', 'mzsys.com', 'mzfmt.com'):
        shutil.copy(os.path.join(BIN, 'Apps', name), SD)
    if not os.path.exists(RAMDISK):
        print('making the Unicard RAM disk (hd1k_cpm3 + hd1k_zpm3)')
        with open(RAMDISK, 'wb') as f:
            for name in ('hd1k_cpm3.img', 'hd1k_zpm3.img'):
                f.write(open(os.path.join(BIN, name), 'rb').read())
    ipl = open(os.path.join(BIN, 'mz800-ipl.bin'), 'rb').read()
    zsys = os.path.join(BIN, 'ZSDOS', 'zsys_wbw.sys')
    tools = [(os.path.join(BIN, 'Apps', n), n.upper()) for n in ('mzsys.com', 'mzfmt.com', 'uc.com')]
    tools.append((zsys, 'ZSYS.SYS'))

    def make(name, fn):
        path = os.path.join(DSK, name)
        if not os.path.exists(path):
            print('making', name)
            fn().save(path)

    make('boot720.dsk', lambda: mkboot(720, ipl, os.path.join(BIN, 'MZ800_std.rom'),
                                       sysimg=open(zsys, 'rb').read(), files=tools))
    make('boot144.dsk', lambda: mkboot(1440, ipl, os.path.join(BIN, 'MZ800_std.rom'),
                                       sysimg=open(zsys, 'rb').read(), files=tools))

    def cpm3():
        ldr, files = image_def(os.path.join(ROOT, 'Source', 'Images', 'fd_cpm3.txt'), 1100 * 1024)
        return mkboot(1440, ipl, os.path.join(BIN, 'MZ800_std.upd'), sysimg=open(ldr, 'rb').read(), files=files)
    make('cpm3_144.dsk', cpm3)
    make('blank720.dsk', lambda: Dsk.new(720, lamac=True))
    make('blank144.dsk', lambda: Dsk.new(1440, lamac=True))
    for name, src in (('lamac_prg.dsk', os.path.join(SIBLING, 'Martin-MZ-FDC', 'work', 'emu', 'prg41.dsk')),
                      ('lamac_sys.dsk', os.path.join(SIBLING, 'MFDC800T', 'DSK', 'CPMv41 System.dsk')),
                      ('martin144.dsk', os.path.join(SIBLING, 'MFDC800T', 'DSK', 'Martin144.dsk'))):
        if not os.path.exists(os.path.join(DSK, name)) and os.path.exists(src):
            print('copying', name)
            shutil.copy(src, os.path.join(DSK, name))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', nargs='?', default='unicard', choices=('unicard', 'floppy', 'hd', 'cpm3'))
    ap.add_argument('--fd0', help='disk in drive 0 instead of the one of the mode (name in mzdev/work/play/dsk)')
    ap.add_argument('--fd1', help='disk in drive 1 (name in mzdev/work/play/dsk)')
    ap.add_argument('--luftner', action='store_true', help='MemExt Luftner instead of PEHU')
    ap.add_argument('--fresh', action='store_true', help='make the SD card, RAM disk and disks again')
    ap.add_argument('--new-ramdisk', action='store_true', help='make only the Unicard RAM disk again')
    ap.add_argument('--autoboot', action='store_true',
                    help='Q + reset starts the RomWBW loader (/unicard/mzfloader.cfg) instead of the Unicard Manager')
    a = ap.parse_args()
    prepare(a.fresh, a.new_ramdisk)
    print('Q + reset starts', unicard_runtime(a.autoboot))
    fd0 = a.fd0 or {'unicard': UNICARD0, 'floppy': 'boot720.dsk', 'hd': 'boot144.dsk',
                    'cpm3': 'cpm3_144.dsk'}[a.mode]
    if fd0 == UNICARD0:
        Dsk.new(720, lamac=True).save(os.path.join(DSK, UNICARD0))   # empty on every start: a reset ends in the ROM
    if fd0 in LAMAC_BOOT:
        print('WARNING: Lamac\'s CP/M formats its RAM disk E: when it boots. It is the same RAM disk as UCRD0:, so the '
              'boot area of slice 0 (CP/M 3, boot loader: 3) gets overwritten. Restore with --new-ramdisk.')
    fd1 = a.fd1 or ('lamac_prg.dsk' if a.mode == 'unicard' else 'blank720.dsk')
    fdd = {0: os.path.join(DSK, fd0), 1: os.path.join(DSK, fd1)}
    exe = 'mz800emu.exe'
    arch = os.path.splitext(exe)[0]
    ov = emu_overrides(arch, PLAY, memext='LUFTNER' if a.luftner else 'PEHU', fill='RANDOM', ramdisk=RAMDISK,
                       unicard_sd=SD, fdd=fdd, fdd_storage='cached')
    ov['BREAKPOINTS']['auto_save'] = '1'       # breakpoints set in the window stay for the next play
    ini = os.path.join(PLAY, arch + '.ini')
    make_ini(ini, os.path.join(EMU_DIR, arch + '.ini'), ov)
    cmd = [os.path.join(EMU_DIR, exe), '--config', ini, '--no-save-ini', '--no-first-run-windows']
    if a.mode == 'unicard':
        cmd += ['--run-mzf', os.path.join(SD, 'mz800-ldr.mzf')]
    print('drive 0: %s, drive 1: %s' % (fd0, fd1))
    print(' '.join(cmd))
    subprocess.Popen(cmd, cwd=EMU_DIR)


if __name__ == '__main__':
    main()
