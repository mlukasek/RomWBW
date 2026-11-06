# MZ-RomWBW: port RomWBW na SHARP MZ-800 s MemExt (PEHU nebo Lüftner)

## Kontext

Autor chce v `E:\SHARP_GIT\MZ-RomWBW` (zatím prázdné) naportovat RomWBW (https://github.com/wwarthen/RomWBW) na
SHARP MZ-800. Chce:
- RAM disk na Unikartě (až 16 MB);
- diskety 360 KB–1,44 MB jako CP/M od Lamače;
- boot z diskety;
- rozumné TPA;
- bonus: disk se soubory ze SD karty Unikarty.

**Zásadní zjištění:** HBIOS potřebuje aspoň 128 KB RAM, přepínané po 32 KB pod pevnou horní 32 KB. Režim bez bank
neexistuje. Základní MZ-800 (64 KB) proto pravý RomWBW neutáhne.

**Rozhodnutí autora (2026-11-06):**
- **MemExt je povinný.** Podporují se **PEHU i Lüftner**, typ se za běhu detekuje.
  - Bez MemExt se zobrazí jen chybová hláška.
  - Autor má PEHU.
- **Diskety:** formáty Lamače (datově kompatibilní) i standardní formáty RomWBW.
- **Repo:** fork RomWBW, větev `mz800`, kód v konvencích RomWBW s cílem PR do upstreamu.

**Výsledek:** RomWBW s TPA 54K (CP/M 2.2/ZSDOS) a 60K (CP/M 3/ZPM3). Pro srovnání Lamač 4.1 má ≈ 55K.

## Ověřená fakta, na kterých plán stojí

- **RomWBW** (d8361fd4, 2026-11-02):
  - ROM-less build (`ROMSIZE=0`): BIOS=$80, IMG0–2=$81–83, RAMD0=$84 (`std.asm:990-1007`).
  - Vzorem nové platformy je port MSX (commit 8983b364, `Source/MSX/msx-ldr.asm`).
  - Ovladač pro WD279x neexistuje (`fd.asm` umí jen 765).
  - Žádné video nekreslí do bitmapy (kostra `gdc.asm`, fonty `Source/Fonts`, terminál `ansi.asm`).
  - Klávesnice 8255 jako vzor: `mky.asm`.
  - Formátování přes HBIOS (DIOFORMAT) nikde není implementováno.
- **MemExt** (`mz800emu/src/emulator/hw-generic/memory/memext.c`):
  - **Oba typy:**
    - port E7h, zápis přes `OUT (C),r`, A12–A15 = stránka 4K adresního prostoru, data = banka;
    - nahrazují celou vnitřní DRAM, mapování ROM/VRAM/CGROM (E0–E6) má přednost;
    - oba mají 512 KB RAM, takže plán bank je pro oba stejný;
    - emulátor bez připojeného MemExt port E7h ignoruje.
  - **PEHU:**
    - data & 3Fh = banka 8 KB;
    - zápis na lichou stránku se zarovná na sudou, okna jsou tedy 8 KB (`memext.c:194-199`);
    - po resetu identita.
  - **Lüftner:**
    - každá stránka 4K samostatně, data 00–7Fh = RAM po 4 KB;
    - 80–FFh = 512 KB flash: čte se, zápis se ztratí (`memext.c:192-193, 276-294`);
    - mapa po zapnutí náhodná;
    - identita po resetu jen s volbou emulátoru `luftner_force_init` (výchozí zapnuto, `memext.c:47-48, 74-78`).
      Jak se chová reálná deska, nevíme.
- **Lamačovy diskety:**
  - log. stopa = válec×2+strana, OFF=4;
  - válec 0 / strana 1 = bootovací stopa 16×256 DD, invertovaná;
  - válce 0–1 jsou DD i na HD disketách.
  - DPB 720K je shodný s `DPB_FD720` RomWBW. 360K se liší jen v AL0.
  - 1.2M/1.44M mají bloky 4K, potřebují nové MID.
- **Unicard:**
  - RAM disk E9h (banka 64K) / EBh (adresa, `OUT (C),r`) / EAh (data, INIR/OTIR), obraz ze `/unicard/ramdisc.cfg`;
  - SD API 50h/51h: SEEK na fw 0.26 nefunguje, v emulátoru ano;
  - RTC 62h/63h;
  - boot přes `mzfloader.cfg` → MZF.

## Architektura

### Paměť (512K MemExt = 16 bank RomWBW, stejné pro PEHU i Lüftner)

| Banka RomWBW | Použití | PEHU (8K banky) | Lüftner (4K banky) |
|---|---|---|---|
| $80 | HBIOS (BOOT=BIOS) | 0–3 | 00–07h |
| $81–$83 | IMG0–IMG2 | 4–15 | 08–1Fh |
| $84–$8B | RAM disk MemExt, 256K | 16–47 | 20–5Fh |
| $8C / $8D / $8E | BUF / AUX / USR | 48–59 | 60–77h |
| $8F | COM, pevně na 8000–FFFF | 60–63 | 78–7Fh |

**Detekce MemExt** (sdílená rutina `mzmemx.asm`, volají ji všechny zavaděče):
1. **Kód zavaděče leží mimo testovanou stránku**, testuje se stránka 4 (4000h).
2. **Je MemExt připojený?** Stránka 4 → banka 20h, zapsat značku M1. Stránka 4 → 21h, zapsat M2. Zpět na 20h:
   - čte M1 → MemExt je;
   - čte M2 → MemExt chybí. Zobrazit hlášku a zastavit.
3. **Který typ?** Stránka 4 → 22h, zapsat M3. Stránka 4 → 20h. Pak `OUT` jen na **stránku 5** s hodnotou 22h:
   - PEHU zarovná zápis na pár 4–5, na 4000h je M3;
   - Lüftner stránku 4 nezmění, na 4000h zůstane M1.
4. **Velikost:** test aliasu nejvyšší banky (PEHU 3Fh, Lüftner 7Fh) proti bance 0. Vyžaduje se 512 KB, jinak hláška.
5. **Mapování a předání HBIOS:**
   - Nastavit celé mapování explicitně (Lüftner může mít po zapnutí náhodnou mapu).
   - Stránku, ve které běží kód, přepnout až po zkopírování kódu do cílové banky (kopie, pak přepnutí na stejnou
     adresu).
   - Typ předat HBIOS v pevném bajtu obrazu. HBIOS ho vypíše v banneru („MemExt PEHU 512K“ / „MemExt Lüftner
     512K“).

**Chybová hláška bez MemExt:**
- Přepnout do režimu MZ-700 (DMD=08h) a vrátit mapu po zapnutí (OUT E4h).
- Text v kódech displeje do textové VRAM D000h, okraj červeně, čekat na reset.
- Text anglicky (upstream), např. „RomWBW requires MemExt (PEHU or Luftner) 512KB“.

**Nový `MM_MZ800` (13)** s variantami podle detekovaného typu:
- **Bank select v proxy** vedle MM_MSX (`hbios.asm` ≈ 1020):
  - PEHU: 4× `OUT (C),A` na E7h (stránky 0, 2, 4, 6), ≈ 150 T;
  - Lüftner: 8× (stránky 0–7, banka 8n…8n+7), ≈ 250 T.
  - Obě zachovají vše kromě AF.
  - Při initu se do proxy nakopíruje varianta podle typu, za běhu se nevětví.
- **Init common banky** vedle bloku MSX (`hbios.asm` ≈ 1975): OUT E0h, OUT E1h, IN E1h, banka $8F na 8000–FFFF.
- E2–E4 už nikdy nepoužívat.
- Ošetřit nepodmíněný `OUT (RTCIO)` (`hbios.asm` ≈ 1621).
- **Později (bonus):** flash Lüftneru (512 KB) jako skutečná ROM, build `ROMSIZE=512` bez nahrávání obrazu. Jen
  pokud deska umí flash programovat.

**Přerušení:**
- INTMODE=2, jediný zdroj PIO PA5 (VBLN 50 Hz, `INT_PIO0A`) → `HB_TIMINT`.
- 8253 přes 8255 PC2 zamaskovat, DFh=0.
- HD přenos z diskety dočasně přepne na IM1 se 7bajtovou ISR na 0038h banky HBIOS, jako to dělá Lamač
  (`Martin-MZ-FDC/docs/cpm41-fdc.md`).

**Mapování VRAM:**
- `IN E0h` mapuje VRAM a CGROM, tedy jen pod DI, krátce.
- Rutiny pro VRAM leží mimo 1000–1FFF a 8000–BFFF: zkopírovat je do heapu HBIOS.

### Cesta bootu

1. **Disketa (IPL MZ-800):**
   - Bootovací stopa nese `03 "IPLPRO"` s +16h = +18h = 0 (ROM-replace) a parametrický blok (formát, název
     souboru obrazu).
   - Stage 2 (≤ 3840 B) přepne vše na RAM a detekuje MemExt (`mzmemx.asm`), bez něj vypíše hlášku.
   - Pak přečte adresář CP/M a nahraje soubor `ROMWBW.SYS` (obraz `.upd`, 128K) do bank RomWBW $80–$83, pak
     `jp 0`.
2. **Unicard:** loader MZF (`mzfldr`) přepne do režimu 800, detekuje MemExt stejnou rutinou a čte obraz ze SD jen
   sekvenčně, bez SEEK. Automatický start přes `mzfloader.cfg`.
3. **Po startu HBIOS:**
   - romldr nabootuje ZSDOS/CP/M 2.2 z IMG0, nebo z oblasti boot disku. Disk boot dává A: = disketa.
   - **Oblast boot disku na disketách MZ:** pro rezervované stopy permutace válec0/h0, válec1/h0, válec1/h1, takže
     vznikne 27 souvislých sektorů pro romldr i SYSCOPY.
   - **Datová oblast** zůstává kompatibilní s Lamačem.
4. **CP/M 3/ZPM3:** CPMLDR z disku (SYSCOPY na disketu nebo slice RAM disku).

### Ovladače (nové soubory v `Source/HBIOS/`)

- **`mzfd.asm`, WD279x/MB8876:**
  - Tabulka funkcí jako `fd.asm`.
  - Invertovat příkazy a status; CPL dat mimo bootovací stopu.
  - Detekce média:
    - READ ADDRESS na válci 0 / straně 1: N=1 → rozložení MZ (Lamač), N=2 → rozložení RomWBW/PC;
    - na válci 2 hustota a počet sektorů;
    - pro emulátor záloha zkusmým READ SECTOR R=18/15/9.
  - **MID:** znovu `MID_FD720` a `MID_FD360`; nové `MID_MZ144`, `MID_MZ120`, které se promítnou do `hbios.inc`,
    DPBMAP a DPB v `cbios.asm`, tabulek CP/M 3 (`diskio.z80`, `biosldr.z80`) a `Apps/copysl`.
  - **Přenos:**
    - DD po bajtech pod DI (≈ 68 T);
    - HD přes přerušení DRQ (HD úprava, DFh);
    - konfigurační přepínač „vždy polling“ pro FDC emulovaný Unikartou (drží /WAIT).
  - Implementovat DIOFORMAT a DIODEFMED (prokládání, bootovací stopa, smíšená hustota).
- **`ucrd.asm`, RAM disk Unikarty** (vzor `rf.asm`):
  - **Velikost:** detekovat aliasem bank.
  - **8/16 MB:** hlásí MID_HD a syntetizuje virtuální MBR na LBA 0 s oddílem 2Eh od LBA 1. Výsledek: 16 MB =
    přesně 2 slice hd1k a surový obraz čtou cpmtools (`wbw_hd1k`, offset 0 a 8M).
  - **4 MB:** `MID_RF`. Menší obrazy odmítnout.
  - **I/O:** jen E9h/EAh/EBh; F8–FA nepoužívat.
- **`mzvdu.asm`, konzole:**
  - 640×200 mono, 80×25, font 8×8 z `Source/Fonts` přes FNT_* zkopírovaný (bitově otočený) do heapu;
  - stínový buffer znaků pro VDARDC;
  - HW scroll (SSA=0, SEA=SW=7Dh, SOF +40 na textový řádek, zápis ve vblanku);
  - kurzor přes EXOR;
  - napojení na `ansi.asm` přes TERM_ATTACH už v PREINIT, aby byly vidět zprávy bootu.
- **`mzkbd.asm`:** matice 10×8 přes 8255, skenování z ticku VBLN, tabulky převodu na kódy RomWBW (podle `mky.asm`).
- **`ucrtc.asm`:** RTC z Unikarty (62h/63h), záloha INTRTC.

### Soubory platformy (konvence RomWBW)

- **Platforma a manažer paměti:** `hbios.inc` (`PLT_MZ800`, požádat Wayna o číslo včas), `std.asm` (`MM_MZ800`),
  `hbios.asm` (bank select, init, řetězec MM, includy ovladačů).
- **Konfigurace:** `cfg_MZ800.asm` z `cfg_TEMPLATE.asm`, `Config/MZ800_std.asm`, `Config/MZ800_dbg.asm` (konzole MIO
  do paměti pro oživení).
- **Build:** `Build.ps1`, `Build.cmd`, `HBIOS/Makefile`, `Source/Build.cmd`, `Source/Makefile`.
- **`Source/MZ800/`:** IPL + stage 2 (`mzipl.asm`), `mzfldr.asm`, detekce MemExt a hláška (`mzmemx.asm`), utility `MZFMT.COM`, `MZSYS.COM`, později
  `UC.COM`. Assembler TASM, jako zbytek RomWBW.

### Vývojové prostředí (mimo PR do upstreamu)

- **Kořen:** `CLAUDE.md`.
- **`mzdev/`:**
  - `docs/` česky: `vyvoj.md`, `rozhodnuti.md`, `plan.md`, `hw-otazky.md`, `hw.md`;
  - `tools/`: Python jen se std. knihovnou:
    - `mzemu.py` převzatý z `MZ-Hlubina/tools/emu`;
    - `mklamac.py`: zapisovač Extended DSK se smíšenými sektory a invertovanou bootovací stopou, z
      `Martin-MZ-FDC/tools/dsk/mkdsk.py` a `cpm41cfg.py`;
    - `vramtext.py`: VRAM → text porovnáním glyfů, kvůli asercím;
    - diskdefs pro cpmtools;
  - `tests/emu/`;
  - `work/` (v `.gitignore`): vlastní ini emulátoru, kopie DSK, SD root Unikarty, obraz RAM disku 16M.
- **Ini emulátoru:**
  - `[MEMEXT] connected=1 type=PEHU`, testy i s `type=LUFTNER` (s `luftner_force_init` 1 i 0) a `connected=0`;
  - `[RAMDISK] mr1r18_type=SRAM`, `mr1r18_size=16M`, vlastní soubor;
  - `[UNICARD] fw_version=1`, vlastní `sd_root`;
  - `[FDC] bus_xlate=invert`, `hd_patch`.
- **Git:** lokální commity průběžně, push (a fork na GitHubu) jen na pokyn.

## Etapy (každá končí ověřitelným milníkem v emulátoru)

| # | Práce | Milník |
|---|---|---|
| 0 | Klon `wwarthen/RomWBW` do MZ-RomWBW, větev `mz800`, `upstream` remote. Plný build beze změn (změřit čas). `mzdev/` s dokumentací, harness emulátoru | Harness spustí emulátor, zapíše a přečte `memext_ram` |
| 1 | PLT_MZ800, MM_MZ800 (varianty PEHU a Lüftner), `mzmemx.asm` (detekce + hláška), cfg + Config, build skripty | `.upd` nahraný přes harness do bank $80–$83, PC=0, banner HBIOS v bufferu MIO, init doběhne s PEHU i s Lüftnerem. Detekce správně určí PEHU / Lüftner / nic |
| 2 | `mzvdu`, `mzkbd`, timer VBLN (IM2) | Na obrazovce menu romldr; `Z` → ZSDOS `A>` na RAM disku MemExt; DIR, TIMER 50 Hz. **První funkční CP/M** |
| 3 | `mzfldr`, `ucrtc`, `ucrd` + diskdef | Boot z emulované Unikarty bez zásahu; TIME z RTC; obraz 16 MB zapsaný v CP/M čitelný cpmtools na PC. **1. test autora na reálném HW** (MZ-800 + PEHU + Unicard) |
| 4 | `mzfd` DD: 360K/720K Lamač i RomWBW | DIR `CPMv41 System.dsk` sedí s `cpm41cfg.py`; zápis ověřený na PC; disketa FD720 RomWBW čitelná |
| 5 | `mzipl` (IPL + stage 2), `MZSYS`, `MZFMT`, DIOFORMAT, permutace boot oblasti | Naformátovat, SYS, studený boot z diskety; romldr disk boot. **2. test na HW** |
| 6 | HD: 1.2M/1.44M Lamač + FD144/FD120, přenos přes DRQ INT | `Martin144.dsk` čtení, zápis a boot. **3. test na HW: časování 55 T/bajt** |
| 7 | CP/M 3/ZPM3, `UC.COM` (DIR/GET/PUT SD, přepnutí obrazu RAM disku přes MOUNT), anglická dokumentace platformy, příprava PR | ZPM3 s 60K TPA; kopie souborů SD ↔ CP/M |
| 8 | Bonus: disk se soubory SD (po opravě SEEK ve fw nebo přes simulaci re-open), boot z RAM disku Unikarty, komprimovaný obraz, RomWBW ve flash Lüftneru (`ROMSIZE=512`) | Podle výsledku průzkumu |

## Ověřování

- **Build:** `Build.cmd MZ800 std` (po prvním plném buildu), výstupy v `Binary/`.
- **Testy v emulátoru:** `python mzdev/tests/emu/run_*.py`. Bez okna přes rouru JSONL: boot, text obrazovky přes
  `vramtext.py`, stisky kláves, kontrola obsahu disků a RAM disku z hosta (cpmtools v `Tools/cpmtools`).
- **Diskety:** jen kopie ve `work/`, `storage_mode=discard` nebo ro. Emulátor umí poškodit hlavičku DSK.
- **Reálný HW má autor.** Body k ověření se sbírají v `mzdev/docs/hw-otazky.md`:
  - PEHU: stav po resetu, párování stránek, dekódování `OUT (C),r`, wait;
  - Lüftner (pokud se k němu někdo dostane): mapa po zapnutí a po resetu, jde-li zapisovat do flash;
  - MZ-800 bez MemExt: dekóduje deska port E7h (zrcadlo E0–E6)? Detekce na E7h zapisuje;
  - DFh polarita a rozpočet 55 T u HD;
  - step rate;
  - layout VRAM 640 a scroll;
  - hrana VBLN na PIO, strobe PA4–PA6 klávesnice;
  - Unicard: verze fw, SEEK, READDIR, RTC, perzistence zápisu RAM disku;
  - přechod z režimu MZ-700 Manageru.

## Rizika a otevřené body

- **Lüftner bez reálné desky:** jeho podpora je ověřená jen proti modelu v emulátoru. Kdyby se reálná deska chovala
  jinak (hlavně mapa po zapnutí), ladilo by se až s ní.
- **HD časování** (55 T z 56 T dostupných) nemá rezervu. Případný wait MemExt by ho rozbil. Záloha: jen DD, nebo
  disky přes Unikartu.
- **IM2:** zbloudilé nevektorované přerušení spadne. Pečlivě maskovat 8253/FDC.
- **Ticky** se během přenosu z diskety ztrácejí: hodiny brát z RTC Unikarty.
- **Místo v heapu HBIOS** (font 2K + stín 4K + buffery) a v proxy ověřit po prvním buildu.
- **Lamač 1.2M DSM=292** přesahuje disk o půl bloku. Ověřit na reálné disketě 4.1.
- **SYSCOPY** na systémovou disketu Lamače ji pro Lamače udělá nebootovatelnou. Zdokumentovat.
- **Upstream:** nové MID zasahují do sdílených tabulek CBIOS a CP/M 3. Číslo platformy domluvit s Waynem.
- **Emulátor** nemodeluje hustotu, časování FDC ani chybu SEEK Unikarty. Co projde v emulátoru, nemusí projít na HW.
