# Zkouška v emulátoru (ručně, s oknem)

Před reálným HW. Všechno běží z kopií v `mzdev/work/play`, originály se nemění.

## Příprava a spuštění

```
python mzdev/tools/emu/play.py [unicard|floppy|hd|cpm3] [--fd0 JMENO] [--fd1 JMENO] [--luftner] [--fresh]
```

- **Nachystá (poprvé, `--fresh` znovu z aktuálního `Binary/`):**
  - SD kartu Unikarty `mzdev/work/play/sd`: zavaděč MZF, `romwbw/MZ800_std.rom`, `uc.com`, `mzsys.com`,
    `mzfmt.com`;
  - RAM disk Unikarty 16 MB: `hd1k_cpm3` + `hd1k_zpm3`;
  - diskety v `mzdev/work/play/dsk`:
    - `boot720.dsk`, `boot144.dsk`: bootovací RomWBW (DD a HD);
    - `cpm3_144.dsk`: CP/M 3;
    - `lamac_prg.dsk`, `lamac_sys.dsk`, `martin144.dsk`: Lamač;
    - `blank720.dsk`, `blank144.dsk`: prázdné.
- **Spustí emulátor s oknem** a vlastním ini: MemExt PEHU (`--luftner` Lüftner), RAM po zapnutí náhodná, řadič
  s HD úpravou. Zápisy na diskety se ukládají.
- **Režimy:**
  - `unicard` (výchozí): zavaděč z Unikarty (emulátor ho spustí jen při startu), v mechanice 0 je prázdná
    `blank720.dsk`, v mechanice 1 `lamac_prg.dsk`;
    - **po resetu** je menu ROM MZ-800 (F, Q, C, M):
      - `Q` nabootuje QuickDisk Unikarty a ten spustí Unicard Manager;
      - v Manageru vyber `mz800-ldr.mzf` a spusť ho;
      - s volbou `--autoboot` spustí `Q` rovnou RomWBW (`/unicard/mzfloader.cfg` ukazuje na zavaděč, jako na
        skutečné Unikartě);
  - `floppy`: zapnutí s `boot720.dsk` v mechanice 0, ROM MZ-800 nabootuje z diskety;
  - `hd`: totéž s `boot144.dsk`;
  - `cpm3`: totéž s `cpm3_144.dsk`.
- `--fd0`, `--fd1` vloží jinou disketu do mechaniky 0 nebo 1 (v mechanice 1 je jinak `blank720.dsk`, v režimu
  `unicard` `lamac_prg.dsk`). Diskety jdou měnit i v menu emulátoru.
- **Reset v režimech `floppy`, `hd`, `cpm3`** vždy znovu nabootuje RomWBW z diskety v mechanice 0.
- **SD karta obsahuje i runtime Unikarty z emulátoru** (`unicard/`: Manager, QuickDisk, `mzfloader.cfg`).
- **Klávesy MZ-800 na PC:** BLANK = `` ` `` (vlevo od 1), ALPHA = `\`, GRAPH = Caps Lock, INST = Insert, DEL =
  Backspace, ESC = Esc nebo End, CTRL = levý Ctrl.

## Doporučené pořadí

1. **`play.py unicard`** (jako 1. test na HW):
   - zavaděč na obrazovce MZ-700, pak menu romldr se seznamem zařízení;
   - `Z` nabootuje ZSDOS;
   - `DIR`, `ASSIGN`, psaní, šipky, BLANK (vyvolá poslední řádek), ALPHA (Caps Lock);
   - `DIR C:` ukáže Lamačovu disketu (mechanika 1), `COPY B:=C:PIP.COM` zapíše na prázdnou disketu v mechanice
     0, `STAT B:DSK:`;
   - `TIME`, `TIMER`.
2. **RAM disk Unikarty:** v menu romldr `3` nabootuje CP/M 3 a `3.1` ZPM3. `DIR`, prompt ZPM3 ukazuje čas.
3. **`play.py floppy`:**
   - ROM ukáže „IPL IS LOADING ROMWBW“, pak zavaděč z diskety a menu;
   - `1` nabootuje ZSDOS z diskety (A: = disketa), `Z` z obrazu;
   - `MZFMT C:` (Y), `MZSYS C:`, `COPY C:ROMWBW.ROM=A:ROMWBW.ROM`, `SYSCOPY C:=A:ZSYS.SYS` (na C: je
     `blank720.dsk`);
   - ukončit emulátor a nabootovat novou disketu: `play.py floppy --fd0 blank720.dsk`.
4. **`play.py hd --fd1 martin144.dsk`:** boot z HD, `DIR C:` Lamačovy HD diskety, `STAT C:DSK:` (1404K).
5. **`play.py cpm3`:** v menu `1` nabootuje CP/M 3 z diskety (60K TPA).
6. **UC.COM** (je na disketách `boot720.dsk` a `boot144.dsk`), např. v režimu `floppy`: `UC DIR`,
   `UC CD ROMWBW`, `UC GET MZ800_STD.ROM B:X.ROM`, `UC PUT A:MZSYS.COM KOPIE.COM`. Soubory se objeví
   v `mzdev/work/play/sd`.
7. **`--luftner`:** totéž s MemExt Lüftner.

## Co sledovat

- Vše, co se chová jinak, než čekáš: rozložení kláves, rychlost, hlášky.
- Hlášky `MZFD0: ERR ...` (disketa) a cokoli, co zamrzne.
- **Emulátor neumí:** hustotu disket, časování řadiče a chybu SEEK Unikarty. Rychlost disket v emulátoru je jiná
  než na stroji. To ukáže až reálný HW.
- **Poškozená disketa:** emulátor umí při zápisu poškodit hlavičku DSK. Pak `--fresh` (smaže a znovu vytvoří SD,
  RAM disk i diskety v `mzdev/work/play`).
