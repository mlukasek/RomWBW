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
- **Další krok, etapa 1:** platforma `PLT_MZ800`, správce paměti `MM_MZ800` s variantami PEHU/Lüftner, detekce
  MemExt `Source/MZ800/mzmemx.asm`, `cfg_MZ800.asm`, `Config/MZ800_std.asm`, `Config/MZ800_dbg.asm` (konzole MIO).
  - **Milník:** `.upd` nahraný přes harness do bank $80–$83, PC=0, banner HBIOS v bufferu MIO.

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
