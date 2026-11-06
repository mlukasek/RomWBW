# Zkouška na reálném MZ-800

## 1. test: boot z Unikarty (od 2026-11-06)

**Potřeba:** MZ-800, MemExt PEHU (nebo Lüftner) 512 KB, Unicard mk3b.

1. **Build:** `Build.cmd MZ800 std` (viz `vyvoj.md`), potom `Source\BuildMZ800.cmd`.
2. **Na SD kartu Unikarty zkopírovat:**
   - `Binary\mz800-ldr.mzf` kamkoli, odkud ho jde spustit z Manageru;
   - `Binary\MZ800_std.rom` (384 KB) **do stejného adresáře** jako zavaděč, nebo do `/romwbw/`.
     - Zavaděč hledá nejdřív v aktuálním adresáři Unikarty, pak v `/romwbw/`.
     - Kam ukazuje aktuální adresář po spuštění z Manageru, nevíme jistě, proto `/romwbw/` je jistota.
3. **Spustit `mz800-ldr.mzf` z Unicard Manageru.**
4. **Na textové obrazovce (režim MZ-700) se má objevit:**

   ```
   ROMWBW LOADER FOR SHARP MZ-800
   MEMEXT: PEHU 512K
   LOADING MZ800-STD.ROM ............
   ```

   (12 teček = 12 bank po 32 KB).
5. **Pak se přepne na 80×25 v režimu 640×200** a ukáže seznam zařízení a výzvu `Boot [H=Help]:`.
6. **Pak zkusit:**
   - `Z` + CR: ZSDOS, `A>`, `DIR` (utility z RAM disku);
   - `C` + CR: CP/M 2.2;
   - `ASSIGN`, `MODE`, `TIMER`, `TIME`;
   - `XM` (bez sériového portu nepůjde).

**Co poslat zpět:**
- **Kde se to zastavilo:** fotka obrazovky.
- **Hlášky zavaděče:** typ MemExt, tečky, případná chyba.
- **Obraz 640×200:**
  - je čitelný, nebliká, scrolluje celý řádek;
  - kurzor je dole v buňce (plný řádek pod znakem).
- **Klávesnice:**
  - písmena: malá jako základ, SHIFT dává velká, ALPHA přepíná Caps Lock;
  - číslice a znaky;
  - CR, DEL (backspace), šipky, CTRL+C;
  - autorepeat (asi po 0,5 s).
- **Jak dlouho trvá načtení** (12 bank).

## Mapování kláves (zatím)

| Klávesa MZ-800 | CP/M |
|---|---|
| písmena | malá, se SHIFT velká, ALPHA = Caps Lock |
| CR | CR (0Dh) |
| DEL | backspace (08h), SHIFT+DEL = Home |
| INST | Insert, SHIFT+INST = Delete |
| šipky | kódy RomWBW → ANSI sekvence |
| F1–F5 | F1–F5, se SHIFT F6–F10 |
| ESC | ESC (1Bh) |
| CTRL+písmeno | 01h–1Ah, CTRL+[ \ ] ^ - = 1Bh–1Fh |
| ↑ (UP_ARROW) | `^`, SHIFT `~` |
| ↓ (DOWN_ARROW) | `` ` `` |
| SHIFT+/ | `_` |
| SHIFT+@ | `` ` `` |
| SHIFT+[ / SHIFT+\ / SHIFT+] | `{` / `}` / `\|` |
| GRAPH, BLANK | zatím nic (GRAPH je rezerva pro vyvolání posledního příkazu) |

Přání k rozložení (podle zvyku z CP/M Lamače) zapsat sem nebo do `rozhodnuti.md`.
