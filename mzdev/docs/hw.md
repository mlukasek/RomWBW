# Hardware MZ-800 pro port RomWBW

Fakta, na kterých port stojí, se zdroji. Co je jen z emulátoru, je tak označené. Otázky k HW jsou v
[hw-otazky.md](hw-otazky.md).

## CPU a paměť

- **CPU:** Z80A, 3,546895 MHz (GDG 17,734475 MHz / 5). Snímek 70 886 T, 50 Hz.
- **Banking v režimu MZ-800** (hodnota zápisu nehraje roli, rozhoduje port):

  | Operace | Účinek |
  |---|---|
  | `OUT (E0h)` | RAM na 0000–1FFF (dolní ROM i CG-ROM pryč, VRAM zůstává) |
  | `OUT (E1h)` | RAM na E000–FFFF |
  | `OUT (E2h)` / `OUT (E3h)` | dolní / horní ROM zpět |
  | `OUT (E4h)` | stav po zapnutí |
  | `OUT (E5h)` / `OUT (E6h)` | „prohibited“ zap/vyp (E000–FFFF čte 1Ah) |
  | `IN A,(E0h)` | CG-ROM na 1000–1FFF **a** VRAM na 8000–BFFF |
  | `IN A,(E1h)` | CG-ROM i VRAM pryč |

  - Kód, který dělá `IN A,(E0h)`, nesmí ležet v 1000–1FFF ani v 8000–BFFF.
  - Zdroje: `..\mz800emu\docs\agent\memory_layout.md`, `..\MZ-Hlubina\docs\hw.md`.

## MemExt (port E7h)

- **Zápis** přes `OUT (C),r`: A12–A15 adresy portu (horní nibble B) = stránka 4K adresního prostoru, data = banka.
- **Nahrazuje celou vnitřní DRAM.** Mapování ROM/VRAM/CG-ROM (E0–E6) má přednost.
- **Zdroj:** jen model v emulátoru `..\mz800emu\src\emulator\hw-generic\memory\memext.c`, dokumentace k HW chybí.

| | PEHU (Peroutka & Hučík) | Lüftner |
|---|---|---|
| RAM | 512 KB, data & 3Fh = banka 8 KB | 512 KB, data 00–7Fh = banka 4 KB |
| Okno | pár stránek 8 KB (lichá stránka se zarovná na sudou) | každá stránka 4 KB zvlášť |
| Flash | ne | 512 KB, data 80–FFh, jen čtení (zápis se ztratí) |
| Po resetu | identita | identita jen s `luftner_force_init`, po zapnutí náhodná mapa |
| Identita stránky p | `OUT` na sudou stránku p, data p/2 | `OUT` na stránku p, data p |

- Ověřeno v emulátoru testem `mzdev/tests/emu/run_memext.py`, viz `vyvoj.md`.

## Disketový řadič (WD279x / MB8876)

| Port | Čtení | Zápis |
|---|---|---|
| D8h | status | příkaz |
| D9h | stopa | stopa |
| DAh | sektor | sektor |
| DBh | data | data |
| DCh | – | motor (bit 7), mechanika (bity 0–1), povolení výběru (bit 2) |
| DDh | – | strana (bit 0) |
| DEh | – | HD/DD (HD úprava) |
| DFh | – | povolení INT od DRQ (HD úprava) |

- **D8–DBh mají invertovaná data** (MB8876 přímo, WD279x přes 8287). Registry DC–DFh se neinvertují.
- **Bez HD úpravy** jen DD. HD potřebuje přerušení od DRQ (nevektorované, IM1). Lamač má rozpočet 55 T na bajt
  z 56 dostupných.
- **IPL MZ-800:**
  - čte válec 0 / **fyzickou stranu 1**, 16×256 DD MFM, data na disku invertovaná;
  - prvních 256 B → CF00h, musí začínat `03 "IPLPRO"`;
  - +16h = +18h = 0 je režim ROM-replace: načte na 1200h, `OUT (E0h)`, zkopíruje na 0000h, skočí na 0000h.
- **Formáty Lamače:**

| Formát | Geometrie | Prokládání | SPT | BSH | DSM | DRM | AL0 | OFF |
|---|---|---|---|---|---|---|---|---|
| 360K | 40×2×9×512 | 1,6,2,7,3,8,4,9,5 | 36 | 4 | 170 | 127 | C0 | 4 |
| 720K | 80×2×9×512 | totéž | 36 | 4 | 350 | 127 | C0 | 4 |
| 1.2M | 80×2×15×512 | 3:1 | 60 | 5 | 292 | 255 | C0 | 4 |
| 1.44M | 80×2×18×512 | 3:1 | 72 | 5 | 350 | 255 | C0 | 4 |

  - log. stopa = válec×2 + strana;
  - válec 0 / strana 1 je vždy bootovací stopa 16×256 DD;
  - na HD disketách je v DD jen bootovací stopa (válec 0 / strana 1), ostatní stopy jsou HD (opraveno 2026-11-07
    podle `Martin144.dsk` a rozboru FORMAT4);
  - mimo bootovací stopu data na disku neinvertovaná (BIOS dělá CPL).
- **Zdroje:** `..\Martin-MZ-FDC\CLAUDE.md`, `docs\testy-emulator.md`, `docs\cpm41-fdc.md`, `..\MZ-1E05\ROM\mz-1e05.asm`.
- **Emulátor:**
  - příkazy proběhnou okamžitě a hustotu nemodeluje;
  - sektory nejvýš 512 B;
  - INT jen přes logiku HD Patch.

## Unicard

- **RAM disk** (stejné porty jako MZ-1R18):

  | Port | Funkce |
  |---|---|
  | E9h (OUT) | banka 64 KB |
  | EBh (OUT) | adresa: nižší bajt = data, vyšší = A8–A15, tedy `OUT (C),r` |
  | EAh (IN/OUT) | data s autoinkrementem (16 bit, zalomí se v bance) |

  - INIR/OTIR fungují, karta drží /WAIT.
  - **Obraz:** soubor podle `/unicard/ramdisc.cfg`, 64 KB–16 MB, mocnina 2. Banky nad velikost se zrcadlí, velikost
    se pozná aliasem.
  - Bajty 0–8 banky 0 s platnou hlavičkou MZ-1R12 → IPL z RAM disku bootuje.
  - Porty F8–FA nepoužívat.
  - **V emulátoru** to dělá MZ-1R18 (`[RAMDISK] mr1r18_type=SRAM`, `mr1r18_size=16M`).
- **SD API** (50h příkaz/status, 51h data):
  - jeden otevřený soubor a jeden adresář;
  - fw 0.26: SEEK nefunguje (v emulátoru ano), READDIR nevrací jméno (použít FILELIST + STAT);
  - RTC: 62h datum, 63h čas.
  - Specifikace: `E:\SAPI_GIT\SAPI_DPI-firmware\docs\unicard.md`.
- **Boot:** Q + reset nabootuje QuickDisk Unikarty (`/unicard/mzfloader.mzq`, zavaděč SC3SROM na 1200h–12A5h)
  a ten spustí MZF z `/unicard/mzfloader.cfg`, standardně Manager (`/unicard/mgr800.mzf`, na 3000h). MZF pro
  `mzfloader.cfg` nesmí ležet na 1200h–12A5h, proto zavaděč RomWBW začíná na 2000h.
- **Zdroje:** `..\unicard-mk3b\src\emu_RAMDISC.c`, `emu_MZFREPO.c`, `..\MZ-UniPi\docs\kompatibilita.md`.

## Video (GDG) a vstupy

- **DMD `OUT (CEh)`:** bit 2 = 640. Režim 640×200 mono používá rovinu I na 8000–BE7F, 80 B na řádek, bit 0 = levý
  pixel.
- **HW scroll** (`LD BC,0nCFh` + `OUT (C),A`):
  - SOF 01/02CFh, SW 03CFh, SSA 04CFh, SEA 05CFh, okraj 06CFh;
  - CPU adresy procházejí stejným přepočtem jako obraz.
  - Podrobně `..\MZ-Hlubina\docs\hw.md`.
- **Status `IN (CEh)`:** bit 6 VBLN (0 = vblank).
- **Klávesnice 8255** (D0–D3): `OUT (D0h)` sloupec 0–9 v PA0–3, `IN (D1h)` řádky, aktivní v 0.
- **Přerušení:**
  - Z80 PIO (FC–FFh) PA5 = VBLN, vektorované;
  - 8253 CTC2 přes 8255 PC2, nevektorované;
  - FDC (HD úprava), nevektorované.
