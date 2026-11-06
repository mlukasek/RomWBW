"""Minimal client of mz800emu over its MCP pipe (JSON lines on stdin/stdout), standard library only.

Taken over from MZ-Hlubina (tools/emu/mzemu.py, itself from MZ-WorldClock and MZ-700-Bad-Apple) and extended
for the RomWBW port: MemExt (PEHU / Luftner), the MZ-1R18 compatible RAM disk (same ports as the Unicard RAM
disk), the Unicard SD card and the floppy controller are configured per run.

The emulator runs headless with our own configuration mzdev/work/emu/<exe>.ini (a copy of the emulator's ini
with our overrides), so nothing in the emulator folder is changed.

Environment: MZ800EMU_DIR (default ..\\mz800emu-2.0.5-preview next to this repo).

    from mzemu import Emu
    with Emu(memext='PEHU') as emu:
        emu.region_write('memext_ram', 0, image)
        emu.run(100)
"""
import base64
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MZDEV = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(MZDEV)
WORK = os.path.join(MZDEV, 'work')
EMU_DIR = os.environ.get('MZ800EMU_DIR', os.path.join(os.path.dirname(ROOT), 'mz800emu-2.0.5-preview'))


def make_ini(path, base, overrides):
    """Copy of the ini `base` with the keys from `overrides` ({section: {key: value}}) replaced or added."""
    src = []
    if base and os.path.exists(base):
        src = open(base, encoding='utf-8', errors='replace').read().splitlines()
    todo = {s: dict(kv) for s, kv in overrides.items()}
    out, section = [], None

    def flush(sec):
        # keys of the section that were not in the base ini go at its end
        for k, v in todo.pop(sec, {}).items():
            out.append('%s = %s' % (k, v))

    for line in src:
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            if section is not None:
                flush(section)
            section = s[1:-1]
            out.append(line)
            continue
        if section in todo and '=' in s:
            key = s.split('=', 1)[0].strip()
            if key in todo[section]:
                out.append('%s = %s' % (key, todo[section].pop(key)))
                continue
        out.append(line)
    if section is not None:
        flush(section)
    for sec in list(todo):
        out.append('[%s]' % sec)
        flush(sec)
        out.append('')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(out) + '\n')


class EmuError(RuntimeError):
    pass


class Emu:
    def __init__(self, exe='mz800emu.exe', memext='PEHU', luftner_force_init=True, ramdisk=None, fill='NULL',
                 unicard_sd=None, unicard_fw=1, fdd=None, hd_patch=True, fdd_storage='discard'):
        """memext: 'PEHU', 'LUFTNER' or None (not connected).
        ramdisk: path of the MZ-1R18 SRAM image (16 MB, the Unicard RAM disk stand-in) or None.
        unicard_sd: host folder used as the Unicard SD card, or None (Unicard not connected).
        unicard_fw: 1 = uc3 (Unicard mk3b fw 0.26, as on real hardware), 0 = uc1.
        fdd: {drive: dsk path}; only copies in mzdev/work should be given (the emulator rewrites DSK headers).
        fdd_storage: 'discard' keeps the image file untouched, 'cached' writes it back on eject / exit; a dict
        {drive: mode} sets it per drive (default 'discard'). Only drives that must be written back should be
        'cached': the emulator may damage the DSK header when it writes the image back."""
        self.exe = exe
        arch = os.path.splitext(exe)[0]
        emu_work = os.path.join(WORK, 'emu')
        ov = {'MEMEXT': {'connected': '1' if memext else '0', 'type': memext or 'PEHU',
                         'luftner_force_init': '1' if luftner_force_init else '0',
                         'flash_filepath': os.path.join(emu_work, 'luftner-flash.dat'),
                         'filling_on_init': fill},
              'RAMDISK': {'mr1r18_pluged': '1' if ramdisk else '0', 'mr1r18_type': 'SRAM', 'mr1r18_size': '16M',
                          'mr1r18_filepath': os.path.abspath(ramdisk) if ramdisk else 'none.dat',
                          'pezik_e8_pluged': '0', 'pezik_68_pluged': '0'},
              'UNICARD': {'connected': '1' if unicard_sd else '0', 'fw_version': str(unicard_fw),
                          'sd_root': os.path.abspath(unicard_sd) if unicard_sd else 'SD-mz800',
                          'managed_fdc': '0x00',
                          # our SD root has no Unicard Manager runtime ({SD}/unicard/); with the check on, the
                          # emulator would wait for a dialog and leave the card disconnected
                          'runtime_check_on_connect': '0'},
              'QDISK': {'mz1f11_connected': '0'},
              'IDE8': {'hdd0_connected': '0', 'hdd1_connected': '0'},
              'FDC': {'connected': '1', 'hd_patch': '1' if hd_patch else '0', 'bus_xlate': 'invert'},
              # breakpoints only for this run: the emulator would otherwise load <arch>-breakpoints.bpt from
              # its folder and save ours there on exit (they then stop every later run)
              'BREAKPOINTS': {'auto_load': '0', 'auto_save': '0',
                              'bpt_file': os.path.join(emu_work, arch + '-breakpoints.bpt')}}
        for n in range(4):
            path = (fdd or {}).get(n, '')
            ov['FDC']['wd279x_fdd%d_dskpath' % n] = os.path.abspath(path) if path else ''
            mode = fdd_storage.get(n, 'discard') if isinstance(fdd_storage, dict) else fdd_storage
            ov['FDC']['wd279x_fdd%d_storage_mode' % n] = mode
        ini = os.path.join(emu_work, arch + '.ini')
        make_ini(ini, os.path.join(EMU_DIR, arch + '.ini'), ov)
        cmd = [os.path.join(EMU_DIR, exe), '--mcp-pipe', '--headless', '--no-first-run-windows', '--no-save-ini',
               '--config', ini]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1, cwd=EMU_DIR,
                                     encoding='utf-8', errors='replace')
        self.req_id = 0
        while True:                   # the emulator is ready after its hello message
            line = self.proc.stdout.readline()
            if not line:
                raise EmuError('emulator did not start: %s' % ' '.join(cmd))
            if line.startswith('{') and json.loads(line).get('type') == 'hello':
                break
        for _ in range(200):          # and then the emulation thread still has to come up
            try:
                self.call('get_state')
                break
            except EmuError:
                time.sleep(0.05)
        self.call('pause')
        self.call('set_speed', {'mode': 'max', 'percent': 100, 'step': 0})   # headless pipe runs ~1 fps otherwise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def call(self, cmd, data=None):
        self.req_id += 1
        req = {'req_id': self.req_id, 'cmd': cmd}
        if data is not None:
            req['data'] = data
        self.proc.stdin.write(json.dumps(req) + '\n')
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise EmuError('emulator closed the pipe (cmd %s)' % cmd)
            if not line.startswith('{'):
                continue
            resp = json.loads(line)
            if resp.get('req_id') != self.req_id:
                continue              # broadcasts and stale responses
            if not resp.get('success', False):
                raise EmuError('%s: %s' % (cmd, resp.get('error', resp)))
            return resp.get('data')

    def close(self):
        if self.proc is None:
            return
        try:
            self.call('shutdown')
        except Exception:
            pass
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc = None

    # helpers -----------------------------------------------------------------------------------------
    def run(self, frames):
        """Run whole frames (at most 1000 per call); returns the emulator's state after the run."""
        res = None
        while frames > 0:
            n = min(frames, 1000)
            res = self.call('run', {'frames': n})
            if res.get('stopped_by') not in ('frames', 'timeout'):
                break             # a breakpoint or the program stopped it
            frames -= res.get('actual_frames', n)
        return res

    def pause(self):
        return self.call('pause')

    def reset(self):
        return self.call('reset')

    def mem(self, addr, length):
        """Bytes in the CPU view (current banking)."""
        out = bytearray()
        while length > 0:
            n = min(length, 256)
            d = self.call('mem_read', {'addr': addr, 'len': n})
            out += base64.b64decode(d['data_b64'])
            addr += n
            length -= n
        return bytes(out)

    def byte(self, addr):
        return self.mem(addr, 1)[0]

    def word(self, addr):
        b = self.mem(addr, 2)
        return b[0] | b[1] << 8

    def poke(self, addr, data):
        """Write bytes to memory (CPU view)."""
        for i in range(0, len(data), 256):
            self.call('mem_write', {'addr': addr + i, 'data_hex': bytes(data[i:i + 256]).hex()})

    def regions(self, refresh=False):
        """{(kind, sub_id): region} of the emulator memory regions (memext_ram, ramdisk_std, vram_phys_plane...)."""
        if refresh or not hasattr(self, '_regions'):
            r = self.call('regions_list')
            self._regions = {(g['kind'], g['sub_id']): g for g in (r.get('regions') or r)}
        return self._regions

    def region(self, kind, offset, length, sub_id=0):
        """Bytes of an emulator memory region by its kind ('vram_phys_plane' with sub_id = plane, 'memext_ram', ...)."""
        rid = self.regions()[(kind, sub_id)]['id']
        out = bytearray()
        while length > 0:
            n = min(length, 1024)
            d = self.call('region_read', {'region_id': rid, 'offset': offset, 'length': n})
            out += base64.b64decode(d['data_b64'])
            offset += n
            length -= n
        return bytes(out)

    def region_write(self, kind, offset, data, sub_id=0):
        """Write bytes straight into an emulator memory region (no CPU, no banking)."""
        reg = self.regions()[(kind, sub_id)]
        if offset + len(data) > reg['size']:
            raise EmuError('region_write %s/%d +%x len %x beyond its size %x'
                           % (kind, sub_id, offset, len(data), reg['size']))
        rid = reg['id']
        for i in range(0, len(data), 32768):
            chunk = bytes(data[i:i + 32768])
            d = self.call('region_write', {'region_id': rid, 'offset': offset + i,
                                           'data_b64': base64.b64encode(chunk).decode()})
            if not d.get('written') or d.get('length') != len(chunk):
                raise EmuError('region_write %s +%x: %s' % (kind, offset + i, d))

    # MemExt RAM ------------------------------------------------------------------------------------
    # The region API splits MemExt RAM into raw 4 KB banks (sub_id = raw bank). For PEHU it enumerates only 64 of
    # them (256 KB, emulator 2.0.5 bug: it counts 8 KB banks but labels them 4 KB), so the upper half of PEHU RAM
    # is reached through the CPU: page 4 (4000h) mapped by OUT (40E7h) and restored to identity afterwards.

    def _memext_type(self):
        name = self.regions()[('memext_ram', 0)]['name']
        return 'PEHU' if 'PEHU' in name else 'LUFTNER'

    def _memext_chunks(self, offset, length):
        while length > 0:
            raw = offset >> 12
            n = min(length, 0x1000 - (offset & 0xFFF))
            yield raw, offset & 0xFFF, n
            offset += n
            length -= n

    def _memext_cpu(self, raw, fn):
        """Run fn(cpu_addr_of_raw_bank_start) with raw 4 KB bank `raw` visible in the CPU view."""
        if self._memext_type() == 'PEHU':
            self.io_out(0x40E7, raw >> 1)            # 8 KB bank into 4000-5FFF
            base = 0x4000 + ((raw & 1) << 12)
            try:
                return fn(base)
            finally:
                self.io_out(0x40E7, 2)               # identity: 8 KB page 2 -> bank 2
        self.io_out(0x40E7, raw)
        try:
            return fn(0x4000)
        finally:
            self.io_out(0x40E7, 4)                   # identity: 4 KB page 4 -> bank 4

    def memext_read(self, offset, length):
        out = bytearray()
        for raw, off, n in self._memext_chunks(offset, length):
            if ('memext_ram', raw) in self.regions():
                out += self.region('memext_ram', off, n, raw)
            else:
                out += self._memext_cpu(raw, lambda base: self.mem(base + off, n))
        return bytes(out)

    def memext_write(self, offset, data):
        pos = 0
        for raw, off, n in self._memext_chunks(offset, len(data)):
            chunk = bytes(data[pos:pos + n])
            if ('memext_ram', raw) in self.regions():
                self.region_write('memext_ram', off, chunk, raw)
            else:
                self._memext_cpu(raw, lambda base: self.poke(base + off, chunk))
            pos += n

    def vram_plane(self, plane, length=16384):
        """Physical VRAM plane (0 = I ... 3 = IV) as stored, i.e. without the HW scroll address shift."""
        return self.region('vram_phys_plane', 0, length, plane)

    def io_out(self, port, value):
        return self.call('io_write', {'port': port, 'value': value})

    def io_in(self, port):
        return self.call('io_read', {'port': port})

    def raster(self):
        return self.call('get_raster_pos')

    def regs(self):
        return self.call('get_registers')

    def set_reg(self, reg, value):
        self.call('set_register', {'reg': reg, 'value': value})

    def set_pc(self, addr):
        self.set_reg('PC', addr)

    def load_mzf(self, path, boot_frames=50):
        """Reset, let the IPL ROM boot (MZ-700 mode), load the MZF; returns its exec address (PC not changed)."""
        self.reset()
        self.run(boot_frames)
        hdr = open(path, 'rb').read(128)
        self.call('media_load_mzf', {'path': os.path.abspath(path)})
        return hdr[0x16] | hdr[0x17] << 8

    def key(self, name, frames=3, gap=3):
        """Hold a key (emulator key name, e.g. 'BREAK', 'SPACE', 'LEFT') for `frames` frames, then release it."""
        self.call('input_press_key', {'key': name})
        self.run(frames)
        self.call('input_release_key', {'key': name})
        self.run(gap)

    def screenshot(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return self.call('screenshot_save_to_file', {'path': os.path.abspath(path)})


if __name__ == '__main__':
    # python mzemu.py CMD '{"arg": value}'
    with Emu() as emu:
        print(json.dumps(emu.call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else None),
                         indent=1)[:5000])
