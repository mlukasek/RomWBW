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
   - `ASSIGN`, `MODE`, `TIMER`;
   - `WDATE` (čas z RTC Unikarty), `WDATE RR MM DD HH MM SS` (nastavení), pak znovu `WDATE` a po vypnutí a
     zapnutí ještě jednou;
   - `UC DIR` (kořen SD karty);
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

## 2. test: diskety DD (od 2026-11-06)

**Potřeba:** totéž jako 1. test, navíc disketový řadič a mechanika 3,5" (výchozí konfigurace: `FD0` i `FD1` jsou 3,5"
HD mechaniky, zatím se čte jen DD).

1. **Diskety:** Lamačova disketa 720K s daty (ne originál, nejlépe kopie) a jedna prázdná DD disketa naformátovaná
   v Lamačově CP/M na 720K (vlastní formátování zatím RomWBW neumí).
2. **Start jako u 1. testu**, v seznamu zařízení mají být `FD0:` a `FD1:` (`Floppy Disk 3.5",DS/HD`).
3. **`Z` + CR**, ZSDOS vypíše přiřazení jednotek, např. `B:=FD0:0`, `C:=FD1:0`.
4. **Zkusit:**
   - `DIR B:` s Lamačovou disketou (seznam souborů, jako v CP/M Lamače);
   - `PIP C:X.COM=B:něco.COM` na prázdnou disketu, pak `DIR C:`;
   - spustit program z diskety (`C:` a pak `X`);
   - `STAT C:DSK:` má ukázat 702 KB, 128 položek adresáře, 4 rezervované stopy;
   - vrátit kopii do Lamačova CP/M a tam ji spustit (kompatibilita zápisu).
5. **Co poslat zpět:**
   - hlášky `MZFD0: ERR ST=.. C=.. H=.. S=..`, pokud se objeví (kolik a kde);
   - jestli motor po 3 s zhasne;
   - jak dlouho trvá `DIR` a kopie (pro odhad rychlosti krokování);
   - co udělá `DIR` na mechanice bez diskety (mělo by to po pár sekundách skončit chybou).

## 3. test: boot z diskety, MZSYS, MZFMT (od 2026-11-07)

**Potřeba:** totéž jako 2. test. Bootovací disketa vznikne jedním ze dvou způsobů:

- **Gotek:** obraz z PC.

  ```
  python mzdev/tools/mzdsk.py mkboot boot.dsk 720 --sys Binary/ZSDOS/zsys_wbw.sys --file Binary/Apps/mzsys.com --file Binary/Apps/mzfmt.com --file Binary/ZSDOS/zsys_wbw.sys=ZSYS.SYS
  ```

  (`ROMWBW.ROM` = `MZ800_std.rom` se přidá sám, `--image Binary/MZ800_std.upd` dá rychlejší boot bez utilit na
  RAM disku.)
- **Na stroji, po startu RomWBW z Unikarty:** prázdná 720K disketa naformátovaná v Lamačově CP/M (nebo
  `MZFMT C:`), pak:

  ```
  MZSYS C:
  COPY C:ROMWBW.ROM=<kde je obraz>
  SYSCOPY C:=ZSYS.SYS
  ```

  Obraz (`MZ800_std.rom` nebo `.upd`) a `ZSYS.SYS` se na stroj dostanou zatím jen přes RAM disk Unikarty: na PC je
  do obrazu RAM disku zapíše cpmtools (`mz_ucrd_0`). `MZSYS.COM` a `MZFMT.COM` taky.

**Postup:**

1. Disketu do mechaniky 0, zapnout. ROM má ukázat „IPL IS LOADING ROMWBW“, pak textová obrazovka zavaděče:

   ```
   ROMWBW FLOPPY LOADER FOR SHARP MZ-800
   MEMEXT: PEHU 512K
   LOADING ............
   ```

2. Pak menu romldr. `1` (FD0) nabootuje ZSDOS z diskety, `A:=FD0:0`. `Z` nabootuje ZSDOS z obrazu.
3. `MZFMT C:` na prázdné disketě (Y potvrdí), pak `DIR C:` (prázdný), `MZSYS C:`.
4. Disketu naformátovanou přes MZFMT zkusit v Lamačově CP/M (DIR, zápis).

**Co poslat zpět:**

- **Boot:** jak dlouho trvá načtení (odhad: `.rom` asi 35 s, `.upd` asi 12 s), případné hlášky „DISK ERROR“;
- **MZFMT:** zda formátuje bez chyb a zda disketu přečte Lamač (formát stopy, mezery GAP, prokládání);
- **romldr z FD0:** boot bez chyb.

## 4. test: HD diskety (od 2026-11-07)

**Potřeba:** řadič s HD úpravou (porty DEh/DFh), mechanika 3,5" HD, HD disketa z Lamačova CP/M (1,44M, např.
kopie systémové nebo datové).

1. **Start z Unikarty nebo z DD diskety**, `Z`, pak s HD disketou v mechanice:
   - `STAT B:DSK:` má ukázat 1404 KB, 256 položek, 32 záznamů na blok, 72 sektorů na stopu, 4 rezervované stopy;
   - `DIR B:`, spustit program z diskety;
   - `COPY C:=B:něco.COM` na druhou HD disketu (formátovanou ve FORMAT4) a zpět v Lamačově CP/M.
2. **Boot z HD diskety:** HD disketa ve formátu Lamače, `MZSYS B:`, `COPY B:ROMWBW.ROM=…`,
   `SYSCOPY B:=ZSYS.SYS`, pak boot z mechaniky 0. Nebo obraz pro Gotek:
   `python mzdev/tools/mzdsk.py mkboot boot144.dsk 1440 --sys Binary/ZSDOS/zsys_wbw.sys`.

**Co poslat zpět:**

- **chyby `MZFD0: ERR ST=..`:** status 04 = LOST DATA (přerušení nestíhá), 10 = sektor nenalezen;
- **jestli po práci s HD jdou hodiny** (`TIMER`) a klávesnice. Během příkazu HD je tik vypnutý, takže hodiny se
  zpožďují;
- **rychlost** (`DIR`, `COPY`);
- **DD disketa v HD mechanice:** detekce nejdřív zkusí HD. Jak dlouho trvá, než se ukáže DIR?

## 5. test: CP/M 3 / ZPM3 a UC.COM (od 2026-11-07)

**CP/M 3 a ZPM3 z RAM disku Unikarty** (nejjednodušší):

1. Na PC složit obraz RAM disku 16 MB ze dvou hotových slice RomWBW:

   ```
   copy /b Binary\hd1k_cpm3.img + Binary\hd1k_zpm3.img ucrd16.img
   ```

2. `ucrd16.img` dát na SD kartu a jeho cestu zapsat do `/unicard/ramdisc.cfg` (jako u 1. testu RAM disku).
3. Start RomWBW z Unikarty. V menu romldr:
   - `3` + CR nabootuje CP/M 3 (UCRD0, slice 0);
   - `3.1` + CR nabootuje ZPM3 (slice 1).

   Číslo jednotky ukazuje seznam zařízení (`Disk 3 UCRD0:`).
4. **Očekávané:** „60K TPA“, prompt `A>` (CP/M 3) nebo `hh:mm A0:SYSTEM>` (ZPM3, čas z Unikarty).

**UC.COM** (soubory SD karty z CP/M) je na RAM disku MD0. Pod ZSDOS a CP/M 2.2 je to A:. Pod CP/M 3 / ZPM3 je
A: bootovací disk a MD0 má jiné písmeno, ukáže ho výpis disků při bootu.

- `UC DIR`, `UC CD ROMWBW`, `UC DIR`;
- `UC GET MZ800_STD.UPD B:R.UPD` (jak dlouho trvá 128 KB?);
- `UC PUT B:R.UPD KOPIE.UPD`, pak na PC porovnat s originálem (PUT ukládá celé záznamy po 128 B).

**Co poslat zpět:** zda CP/M 3 a ZPM3 naběhnou, rychlost GET/PUT, chybová hlášení UC.

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
| BLANK | na prázdném řádku vyvolá poslední zadaný řádek (jako CP/M Lamače) |
| GRAPH | zatím nic (u Lamače mrtvá klávesa pro české znaky) |

Přání k rozložení (podle zvyku z CP/M Lamače) zapsat sem nebo do `rozhodnuti.md`.
