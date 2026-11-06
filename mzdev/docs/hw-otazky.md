# Otázky k ověření na reálném HW

Co nejde ověřit v emulátoru. Odpovědi zapisovat sem s datem a pak promítnout do `hw.md` / kódu.

## MemExt

- **PEHU:**
  - Stav mapování po zapnutí a po resetu: identita (8K stránka p → banka p)? Emulátor to tak modeluje.
  - Párování stránek: zápis na lichou stránku (A12 = 1) přepne celý pár 8 KB? Na tom stojí detekce typu.
  - Dekóduje port E7h jen A0–A7, nebo i něco z A8–A11? Používáme `OUT (C),r` s B = stránka << 4.
  - Přidává přístup do RAM MemExt wait stavy? To je důležité pro časování HD disket.
  - Pracuje MemExt i s ROM IPL a s VRAM bez omezení? Emulátor: mapování E0–E6 má přednost.
- **Lüftner** (pokud se k němu někdo dostane):
  - Mapa po zapnutí a po resetu. Emulátor má volbu `luftner_force_init`, po zapnutí náhodnou mapu.
  - Jde zapisovat do flash (banky 80–FFh)? Jaký je to čip?
- **MZ-800 bez MemExt:** reaguje deska nějak na zápis na port E7h (zrcadlo E0–E6)? Detekce na E7h zapisuje.

## Disketový řadič

- Polarita DFh (povolení INT od DRQ) a rozpočet 55 T/bajt u HD s ISR na 0038h.
- Step rate mechanik, takt WD279x.
- Mají autorovy řadiče HD úpravu (DEh/DFh)? Které mechaniky a formáty jsou k dispozici?
- **`mzfd.asm` (DD, od 2026-11-06), co emulátor neověří:**
  - **Přenos dotazováním:** čtení 87 T, zápis 90 T na bajt při DI. Stihne to DD bez LOST DATA, i když MemExt
    přidává wait stavy?
  - **Okna `EI / NOP / DI` při čekání na sektor:** obsluha tiku (sken klávesnice) trvá déle než 32 µs. Když DRQ
    přijde během ní, první bajt propadne a sektor se opakuje. Jak často se to stává (hlášky `MZFD0: ERR`)?
  - **Krok r=00:** 6 ms na WD279x/MB8876 v DD i na WD1772. Zvládnou ho autorovy mechaniky? Jinak `MZFDSTEP`.
  - **Časy:** start motoru 500 ms, usazení hlavy 15 ms. Lamač 4.1 má 189 ms a ≈ 3 ms.
  - **Strana:** DDh bit 0 = 1 je fyzická strana 1 (podle emulátoru a ROM MZ-1E05). Sedí to?
  - **Bez diskety v mechanice:** detekce čeká na timeout ≈ 2 × 3,7 s. Hlásí se to rozumně (chyba výběru disku)?
  - **Výměna diskety:** CP/M ji pozná až po ^C (nové přihlášení jednotky). Detekce běží při každém přihlášení.
- **Boot z diskety a formátování (od 2026-11-07):**
  - **IPL v ROM MZ-800 v normálním režimu:** hlavička s načtením i startem na $1200 (Lamač používá ROM-replace).
    Je to v ROM MZ-800 stejné jako v ROM MZ-1E05?
  - **WRITE TRACK dotazováním:** 66 T na bajt, 99 T na konci běhu. První bajt musí přijít do 3 bajtových časů po
    příkazu (zavaděč čeká jen na BUSY).
  - **Stopa 9 × 512:** GAP 4a 80, GAP 1 50, GAP 2 22, GAP 3 84, prokládání jako FORMAT4. Bootovací stopa 16 × 256
    s GAP 3 50. Vejde se to na stopu a přečte to Lamač?
  - **Rychlost zavaděče IPL:** sektory v logickém pořadí, odhad 11 KB/s.

## Video a vstupy

- Layout VRAM v režimu 640×200 a HW scroll (SSA=0, SEA=SW=7Dh, krok SOF 40 na textový řádek).
- Hrana a polarita VBLN na Z80 PIO PA5 jako tik 50 Hz.
- Strobe klávesnice: PA4–PA6 držet v 0, nebo `F0h | sloupec`? TRM a emulátor se liší.

## Unicard

- Verze firmwaru na autorově kartě (0.26?). Funguje SEEK? Ve fw 0.26 podle zdrojáků ne, v emulátoru ano.
- READDIR, RTC (příkazy 62h/63h), perzistence zápisu RAM disku (obraz ze `ramdisc.cfg`), max. velikost obrazu 16 MB.
- Přechod z režimu MZ-700, ve kterém Unicard Manager spouští MZF, do režimu MZ-800.
- Emuluje Unicard i FDC s přerušením od DRQ (HD úprava), nebo jen polling?
