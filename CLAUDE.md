# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MZ-RomWBW: kontext projektu

Port **RomWBW** (https://github.com/wwarthen/RomWBW) na **SHARP MZ-800**. Repo je fork upstreamu, práce je ve větvi
`mz800`.

- **Cíl:** CP/M (ZSDOS, CP/M 2.2, CP/M 3/ZPM3) s TPA 54K/60K. Disky:
  - RAM disk Unikarty (až 16 MB);
  - diskety 360K–1,44M datově kompatibilní s CP/M Lamače i standardní formáty RomWBW;
  - boot z diskety a z Unikarty;
  - bonus: disk se soubory ze SD karty Unikarty.
- **MemExt je povinný** (HBIOS potřebuje přepínanou RAM). Podporuje se **PEHU i Lüftner** (512 KB), typ se za
  běhu detekuje. Bez MemExt zavaděč jen vypíše chybovou hlášku. Autor má PEHU.
- **Upstream:** kód platformy v konvencích RomWBW (TASM, `cfg_MZ800.asm`, `Config/MZ800_*.asm`), aby šel nabídnout
  jako PR. `mzdev/` a tento soubor do PR nepatří.

Autor: Martin Lukášek. Komunikace **česky**.

## Kde co je

- **Pro práci začni v `mzdev/docs/vyvoj.md`:** stav, další krok, build, testy, pasti.
- `mzdev/docs/plan.md`: architektura a etapy (schválený plán 2026-11-06).
- `mzdev/docs/rozhodnuti.md`: rozhodnutí autora a technická rozhodnutí s důvody. Nová dopisovat.
- `mzdev/docs/hw.md`: hardware pro port (paměť, MemExt, FDC, Unicard, GDG, klávesnice, přerušení) se zdroji.
- `mzdev/docs/hw-otazky.md`: co má autor ověřit na reálném MZ-800.
- `mzdev/tools/emu/mzemu.py`: ovládání emulátoru přes rouru MCP (MemExt, RAM disk, Unicard SD, FDC).
- `mzdev/tests/emu/`: testy v emulátoru. `mzdev/work/` je lokální (v `.gitignore`).
- **Kód platformy (vzniká):** `Source/HBIOS/cfg_MZ800.asm`, `Source/HBIOS/Config/MZ800_*.asm`, ovladače
  `Source/HBIOS/mz*.asm` a `uc*.asm`, zavaděče a utility v `Source/MZ800/`.

## Pravidla

- **Jazyk:** kód, komentáře a skripty **anglicky**, dokumentace v `mzdev/docs/` **česky**.
- **Konvence RomWBW:**
  - TASM (`Tools/tasm32`), konce řádků **CRLF** jako zbytek `Source/`;
  - nové soubory platformy po vzoru portu MSX (commit 8983b364);
  - do sdílených souborů (`hbios.asm`, `std.asm`, `cbios.asm`…) zasahovat co nejméně a podmíněně
    (`PLATFORM == PLT_MZ800`).
- **Git:**
  - lokální commity průběžně;
  - push a založení forku na GitHubu jen na pokyn autora;
  - remote `upstream` = wwarthen/RomWBW.
- **Sousední složky** (`..\RomWBW`, `..\mz800emu*`, `..\unicard-mk3b`, `..\Martin-MZ-FDC` …) jen číst.
- **Necommitovat** ROM ani CG-ROM Sharp a nic z nich odvozeného.
- **Python 3:** nástroje a testy jen se standardní knihovnou.
- **Měřit, nehádat:** chování ověřovat v emulátoru.
- **Reálný HW má autor.** Otázky sbírat v `mzdev/docs/hw-otazky.md`.

## Build

- **Pasti harnessu:**
  - Claude Code spouští příkazy s proměnnou `NoDefaultCurrentDirectoryInExePath=1`, takže `cmd` nenajde dávky v
    aktuální složce (`call Build` v dávkách RomWBW selže).
  - Na pozadí se navíc nedědí pracovní složka.
- **Spouštět vždy takto:**
  `cmd /d /c "set NoDefaultCurrentDirectoryInExePath=&& cd /d E:\SHARP_GIT\MZ-RomWBW && Build.cmd MZ800 std"`
  (výstup přesměrovat do souboru).
- **První build** v čistém klonu musí projít celý: sdílené části, CP/M a obrazy. Pak stačí jen HBIOS:
  `cd /d Source\HBIOS && Build.cmd MZ800 std`.
  - **Po něm vždy `Source\BuildMZ800.cmd`:** build HBIOS dá do `MZ800_std.rom` standardní A:. Disk A: pro
    MZ-800 (bez FDU, FLASH, RTC; s UC, MZSYS, MZFMT, WDATE) do `.rom` vloží až `Source/MZ800/Build.cmd`.
  - Chyby cpmtools hledat ve výpisu: kód návratu byl i po chybě `cpmcp` 0.
- **Výstupy** jsou v `Binary/`: `MZ800_std.rom`, `.upd`, `.com`.
- Plný build (sdílené části + jedna platforma) trvá asi 1:20 min.

## Testy

- `python mzdev/tests/emu/run_memext.py`: harness, mapování MemExt (PEHU, Lüftner, žádný).
- `python mzdev/tests/emu/run_hbios.py`: start HBIOS z `Binary/MZ800_std.upd` (po buildu `MZ800 std`).
- `python mzdev/tests/emu/run_console.py [PEHU|LUFTNER] [--random]`: konzole, klávesnice, tik, ZSDOS.
- `python mzdev/tests/emu/run_blank.py`: historie příkazů BLANK / SHIFT+BLANK.
- `python mzdev/tests/emu/run_loader.py`: zavaděč MZF z Unikarty až po ZSDOS (po `Source\BuildMZ800.cmd`).
- Disky: `run_ucrd.py` (RAM disk Unikarty), `run_fd.py` (DD), `run_hd.py` (HD), `run_fmt.py` (MZFMT).
- Boot a systémy: `run_ipl.py` (boot z diskety, MZSYS, asi 15 min), `run_cpm3.py`, `run_rwimg.py`, `run_uc.py`,
  `run_drva.py` (obsah A:, WDATE, UC z A:).
- Zkouška na reálném HW: `mzdev/docs/test-hw.md`.
- Další testy podle etap v `mzdev/docs/vyvoj.md`.
- **Emulátor spouštět vždy jen jeden najednou** (sdílený ini v `mzdev/work/emu`). Dlouhé testy na pozadí s výstupem
  do souboru.
- **Python s `'\n'` v řetězcích** neupravovat přes heredoc v Bash (shell ho převede na konec řádku), ale nástrojem
  Edit.
- **Soubory s diakritikou upravovat nástrojem Edit/Write**, ne přes `Get-Content`/`Set-Content` v PowerShellu 5.1. Ten
  čte UTF-8 bez BOM jako ANSI a rozbije češtinu.
