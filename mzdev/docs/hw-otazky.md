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

## Video a vstupy

- Layout VRAM v režimu 640×200 a HW scroll (SSA=0, SEA=SW=7Dh, krok SOF 40 na textový řádek).
- Hrana a polarita VBLN na Z80 PIO PA5 jako tik 50 Hz.
- Strobe klávesnice: PA4–PA6 držet v 0, nebo `F0h | sloupec`? TRM a emulátor se liší.

## Unicard

- Verze firmwaru na autorově kartě (0.26?). Funguje SEEK? Ve fw 0.26 podle zdrojáků ne, v emulátoru ano.
- READDIR, RTC (příkazy 62h/63h), perzistence zápisu RAM disku (obraz ze `ramdisc.cfg`), max. velikost obrazu 16 MB.
- Přechod z režimu MZ-700, ve kterém Unicard Manager spouští MZF, do režimu MZ-800.
- Emuluje Unicard i FDC s přerušením od DRQ (HD úprava), nebo jen polling?
