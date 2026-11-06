# Vývoj

- **Plán etap a architektura:** [plan.md](plan.md).
- **Rozhodnutí s důvody:** [rozhodnuti.md](rozhodnuti.md).
- **Hardware pro port:** [hw.md](hw.md).
- **Ověření na reálném HW:** [hw-otazky.md](hw-otazky.md).

## Stav (2026-11-06)

- **Etapa 0 je hotová:**
  - repo je klon `wwarthen/RomWBW` (d8361fd4, 2026-11-02), větev `mz800`, remote `upstream`;
  - plný build beze změn prošel (`Build.cmd MSX std`, 1:17 min);
  - harness emulátoru umí MemExt, RAM disk, Unicard SD a FDC;
  - test `run_memext.py` ověřil 512 KB a mapování E7h u PEHU, Lüftneru i bez MemExt.
- **Etapa 1 (jádro HBIOS) je hotová:**
  - `PLT_MZ800` (30), `MM_MZ800` (13), `cfg_MZ800.asm` (odvozený z MSX), `Config/MZ800_std.asm`, zápis do
    `Build.ps1`, `Build.cmd` a `Makefile`;
  - **proxy, bank select:** smyčka OUT na E7h, ve výchozím stavu PEHU (krok stránky $20, 4 okna). Pro Lüftner
    HBIOS při startu přepíše `HBX_MZX8` na `RLCA` a `HBX_MZSTEP` na $1008. Rozepsaná varianta se do proxy nevešla:
    nezbyl by zásobník přerušení (teď má 38 B);
  - **init v `HB_START`** (před instalací proxy):
    - OUT E0h/E1h, IN E1h;
    - detekce typu na stránce $C bankami $20/$22, původní bajty se vrací;
    - namapování `BID_COM` na 8000–FFFF;
    - bez MemExt červený okraj a HALT;
  - zápisy do `RTCIO` jsou pro MZ-800 vypnuté (`PLATFORM != PLT_MZ800`);
  - v bance HBIOS zbývá 24,5 KB, `INTMODE=0` (přerušení až s časovačem v etapě 2).
  - **Ověřeno** (`run_hbios.py`): s PEHU i Lüftnerem HBIOS doběhne a romldr v bance $8E volá HBIOS (bez konzole
    dostává chybu jednotky). Bez MemExt skončí v `MZ_NOMX`.
- **Detekce v zavaděčích** (`Source/MZ800/mzmemx.asm` s hláškou v režimu MZ-700) se dělá spolu se zavaděčem MZF
  v etapě 3, samostatně by nešla vyzkoušet.
- **Další krok, etapa 2:** konzole `mzvdu.asm` (640×200, 80×25, font 8×8, HW scroll) a `mzkbd.asm`, časovač VBLN
  (IM2). **Milník:** menu romldr na obrazovce, `Z` → ZSDOS `A>`.

## Build

- **Z Claude Code** vždy takto (vysvětlení v `CLAUDE.md`):

  ```
  cmd /d /c "set NoDefaultCurrentDirectoryInExePath=&& cd /d E:\SHARP_GIT\MZ-RomWBW && Build.cmd MZ800 std" *> log
  ```

- **Bez parametrů** `Build.cmd` čeká na interaktivní volbu platformy. Na pozadí to zamrzne.
- **Upstream nechává** po buildu nesledované `*.err` a `Source/HBIOS/hbios_env.cmd`. Jsou v `.git/info/exclude`
  (lokálně, necommituje se).

## Emulátor

- **Spouští** se přes `mzdev/tools/emu/mzemu.py`: `Emu(memext='PEHU'|'LUFTNER'|None, ramdisk=…, unicard_sd=…,
  fdd={0: …})`.
  - Vlastní ini v `mzdev/work/emu/`, ve složce emulátoru se nic nemění.
- **Chyba emulátoru 2.0.5:** `regions_list` dává u PEHU jen 64 oblastí `memext_ram` po 4 KB, tedy 256 KB.
  - Horní polovinu RAM PEHU čte a zapisuje `memext_read` / `memext_write` přes CPU: stránka 4 přes `OUT (40E7h)`, pak
    zpět identita.
  - U Lüftneru je oblastí 128, vidět je všech 512 KB.
- **Diskety:** jen kopie ve `mzdev/work/`, výchozí `storage_mode=discard`. Emulátor umí poškodit hlavičku DSK.
- **Unicard v emulátoru:**
  - SEEK funguje, na reálné fw 0.26 ne;
  - RAM disk Unikarty zastupuje MZ-1R18 SRAM 16M na stejných portech.

## Testy

- `python mzdev/tests/emu/run_memext.py`: MemExt PEHU/Lüftner/žádný, 512 KB přes harness, párování stránek PEHU.
- `python mzdev/tests/emu/run_hbios.py`: `Binary/MZ800_std.upd` přímo do MemExt, start HBIOS (PEHU, Lüftner, bez
  MemExt). Předpokládá hotový build `MZ800 std`.
- **Symboly:** TASM nedělá soubor symbolů. `mzdev/tools/emu/tasmlst.py` vytáhne adresy návěští z `.lst`, např.
  `Source/HBIOS/hbios_rom.lst`, `romldr.lst`.
- **Proměnné HBIOS** číst přes `memext_read` z banky $80 (offset 0), ne přes pohled CPU. Ten ukazuje banku, která
  je zrovna namapovaná.

## Pasti

- **Git Bash a Python s heredocem:** úprava `Makefile` přes `python -I - <<EOF` nenašla řetězec, který tam je.
  Úpravy souborů se CRLF dělat skriptem spuštěným z PowerShellu.
- **TASM při přetečení proxy** (kód za $FF00) nehlásí chybu, jen přestane psát listing a `.bin` nevznikne. Kontrola:
  `HBIOS INT STACK space` ve výpisu buildu.
