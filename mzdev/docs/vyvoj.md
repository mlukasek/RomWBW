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
- **Etapa 2, první část je hotová (2026-11-06): konzole a klávesnice.**
  - **`Source/HBIOS/mzv.asm`** (modul MZV, VDA typ `VDADEV_MZV` = 9):
    - 640×200 mono, 80×25, font 8×8 z obrazu (komprimovaný, LZSA2), zrcadlený do 2 KB v modulu;
    - scroll přes SOF (40 jednotek na textový řádek);
    - kurzor = invertovaný spodní řádek buňky;
    - atributy reverse a underline;
    - VDACPY: celé řádky přes LDIR, jinak po buňkách s ohledem na směr;
    - VDARDC není.
  - **`Source/HBIOS/mzkbd.asm`** (modul MZK):
    - matice přes 8255, sken při dotazu na stav (zatím bez časovače, bez autorepeat);
    - SHIFT, CTRL, ALPHA = Caps Lock;
    - kurzorové klávesy, INST/DEL, F1–F5 na kódy RomWBW ($F0–$F9, $E0–$E9);
    - tabulky z `mzdev/tools/mzkbdtab.py`.
  - **Zapojení:**
    - `MZVENABLE` (cfg_MASTER), `MZKENABLE` (std.asm), include v `hbios.asm`;
    - `MZVENABLE` v podmínce dekompresoru LZSA2;
    - `ROMFONTS=TRUE`, `USELZSA2=TRUE` v `cfg_MZ800.asm`;
    - název `MZV` v `Apps/devlist`.
  - **Ověřeno** (`run_console.py`, PEHU i Lüftner, nulová i náhodná RAM):
    - menu romldr se seznamem zařízení;
    - `z` → `ZSDOS v1.1, 54.0K TPA`, `A>`;
    - `DIR` na RAM disku;
    - scroll.
- **Etapa 2 je hotová (2026-11-06): časovač a klávesnice z tiku.**
  - **Časovač:** `INTMODE=2`, `MZVTIMENABLE`, typ `TM_MZV` (8) v `std.asm`.
    - Z80 PIO kanál A v bitovém režimu, přerušení při sestupu PA5 (VBLN), vektor `INT_PIO0A`.
    - Kanál B má přerušení vypnutá, 8253 je zamaskovaný přes 8255 PC2=0.
  - **Klávesnice:** sken matice na každém tiku (háček `VEC_TICK`), fronta 8 kláves, autorepeat po 0,5 s, pak každé 3
    tiky.
  - **Ověřeno:** 100 tiků za 100 snímků, podržené X dá 13 znaků, DEL maže.
- **Další krok, etapa 3:** zavaděč MZF z Unikarty (`Source/MZ800/`, s detekcí MemExt a hláškou), RTC z Unikarty, RAM
  disk Unikarty.

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
- `python mzdev/tests/emu/run_console.py [PEHU|LUFTNER] [--random]`: konzole a klávesnice, boot ZSDOS, DIR, scroll.
  Text obrazovky čte `mzdev/tools/emu/vramtext.py` (glyfy z `Source/Fonts/font8x8u.bin`).
- **Symboly:** TASM nedělá soubor symbolů. `mzdev/tools/emu/tasmlst.py` vytáhne adresy návěští z `.lst`, např.
  `Source/HBIOS/hbios_rom.lst`, `romldr.lst`.
- **Proměnné HBIOS** číst přes `memext_read` z banky $80 (offset 0), ne přes pohled CPU. Ten ukazuje banku, která
  je zrovna namapovaná.

## Pasti

- **Git Bash a Python s heredocem:** úprava `Makefile` přes `python -I - <<EOF` nenašla řetězec, který tam je.
  Úpravy souborů se CRLF dělat skriptem spuštěným z PowerShellu.
- **TASM při přetečení proxy** (kód za $FF00) nehlásí chybu, jen přestane psát listing a `.bin` nevznikne. Kontrola:
  `HBIOS INT STACK space` ve výpisu buildu.
- **TASM 3.2 zkrátí argument makra na 16 znaků.**
  - `PRTS("dlouhý text$")` pak do `.TEXT` vloží zbytek řádku definice makra i s komentářem.
  - `PRTSTRD` tiskne až po náhodné `$` a návrat skočí doprostřed kódu.
  - Delší texty tisknout přes `PRTX(label)` s řetězcem v datech.
- **Každý soubor ovladače v HBIOS musí být modul** s hlavičkou `.DW SIZ_x` / `.DW x_INITPHASE` a koncem `END_x` /
  `SIZ_x`.
  - `MODINIT` prochází moduly podle velikostí za sebou.
  - Soubor bez hlavičky se vezme jako hlavička a HBIOS skočí do dat. Pak se restartuje dokola, s nulovou RAM jinak
    než s náhodnou.
- **CG-ROM při `IN A,($E0)`:**
  - kód a data používaná při namapované VRAM musí ležet nad $2000;
  - `mzv.asm` si za hlavičkou modulu případně udělá výplň do $2000 a hlídá to při překladu;
  - zásobník HBIOS je na $0200–$04FF, takže je mimo.
- **Emulátor a obsah RAM:** `Emu(fill='NULL')` je výchozí kvůli opakovatelnosti. `run_console.py --random` zkouší
  náhodnou RAM po zapnutí jako na skutečném stroji.
- **Font v obrazu je komprimovaný** (LZSA2). `FNT_SELECT` ho rozbalí jen pro ovladače v podmínce `#IF ((CVDUENABLE |
  … | MZVENABLE) & USELZSA2)` v `hbios.asm`.
