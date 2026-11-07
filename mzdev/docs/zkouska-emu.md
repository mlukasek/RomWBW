# Zkouška v emulátoru (ručně, s oknem)

Před reálným HW. Všechno běží z kopií v `mzdev/work/play`, originály se nemění.

## Příprava a spuštění

```
python mzdev/tools/emu/play.py [unicard|floppy|hd|cpm3] [--fd0 JMENO] [--fd1 JMENO] [--luftner] [--fresh]
                               [--new-ramdisk] [--autoboot]
```

- **Nachystá (poprvé, `--fresh` znovu z aktuálního `Binary/`, `--new-ramdisk` jen RAM disk):**
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
    `unicard0.dsk` (při každém spuštění znovu prázdná, aby reset skončil v menu ROM), v mechanice 1
    `lamac_prg.dsk`;
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
   - `WDATE` ukáže čas z RTC Unikarty. `WDATE RR MM DD HH MM SS` ho nastaví, emulátor ale nastavení neumí.
     `TIMER` ukáže tik 50 Hz.
   - `UC DIR` vypíše kořen SD karty (`UC` je na A: stejně jako `MZSYS` a `MZFMT`).
   - **Ne Lamačův `TIME` z C:**, viz „Programy z Lamačových disket pod RomWBW“ níže.
2. **RAM disk Unikarty:** v menu romldr `3` nabootuje CP/M 3 a `3.1` ZPM3. `DIR`, prompt ZPM3 ukazuje čas.
3. **`play.py floppy`:**
   - ROM ukáže „IPL IS LOADING ROMWBW“, pak zavaděč z diskety a menu;
   - `1` nabootuje ZSDOS z diskety (A: = disketa), `Z` z obrazu;
   - po `1` je A: disketa, B: RAM disk MD0 (s `COPY` a `SYSCOPY`), C: mechanika 1 (`blank720.dsk`). Písmena ukáže
     výpis `A:=FD0:0`… při bootu;
   - `MZFMT C:` (Y), `MZSYS C:`, `B:COPY C:ROMWBW.ROM=A:ROMWBW.ROM`, `B:SYSCOPY C:=A:ZSYS.SYS` (Y);
   - ukončit emulátor a nabootovat novou disketu: `play.py floppy --fd0 blank720.dsk`.
4. **`play.py hd --fd1 martin144.dsk`:** boot z HD, `DIR C:` Lamačovy HD diskety, `STAT C:DSK:` (1404K).
5. **`play.py cpm3`:** v menu `1` nabootuje CP/M 3 z diskety (60K TPA).
6. **UC.COM** (na A: a na disketách `boot720.dsk` a `boot144.dsk`), např. v režimu `floppy`: `UC DIR`,
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
- **Lamačovo CP/M přepíše RAM disk Unikarty:**
  - RAM disk MZ-1R18 v emulátoru (stejné porty jako RAM disk Unikarty) bere Lamačovo CP/M jako svůj RAM disk
    `E:`. Při bootu si ho naformátuje: přepíše první 4 KB, tedy bootovací oblast slice 0 (ověřeno 2026-11-07,
    stejných 154 bajtů z `lamac_prg.dsk` i `lamac_sys.dsk`).
  - V menu romldr pak `3` hlásí „No boot record“. `3.1` (ZPM3) a soubory ve slice 0 zůstanou. Zápis na `E:`
    v Lamačově CP/M by ale poškodil i je.
  - Lamačovo CP/M nabootuje z `lamac_prg.dsk`, `lamac_sys.dsk` a `martin144.dsk` v mechanice 0. `play.py` při
    nich varuje.
  - **Oprava:** `--new-ramdisk` vytvoří RAM disk znovu (diskety a SD karta zůstanou).

## Programy z Lamačových disket pod RomWBW

Obecné programy pro CP/M z Lamačových disket běží. Programy, které sahají do paměti nebo BIOSu Lamačova CP/M, ne.
RomWBW má CP/M 2.2 jinde: CCP `$D000`, BDOS `$D800` (vstup `$D806`), CBIOS `$E600–$FDFF`.

- **`TIME.COM`** (Lamač 1988) čte a zapisuje hodiny Lamačova BIOSu na `$EA40–$EA42` (sekundy od půlnoci). Pod
  RomWBW je tam kód CBIOS, takže ukáže nesmysl.
  - **Čas jím nenastavovat:** přepsal by 3 bajty CBIOS.
  - Místo něj `WDATE` (viz výše).
- **`UNIUTIL.COM`** (podpora Unikarty, program autora tohoto portu, ne Lamačův; Turbo Pascal 3, zdroják `UU.PAS`
  na disketě) potřebuje BDOS aspoň na `$D942`. Pod ZSDOS a CP/M 2.2 (`$D806`) skončí hláškou „Not enough memory“.
  - **Pod CP/M 3 funguje** (autor, emulátor, 2026-11-07).
  - Jeho nastavení času CP/M zapisuje na `$EA40` (hodiny Lamačova BIOSu).
  - Nová verze pro RomWBW: možná časem (autor).
  - Soubory SD karty a obraz RAM disku obslouží `UC` (`DIR`, `CD`, `GET`, `PUT`, `MOUNT`), RTC Unikarty `WDATE`.
