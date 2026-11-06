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
- **Etapa 3, zavaděč z Unikarty je hotový (2026-11-06):** `Source/MZ800/mzfldr.asm` → `Binary/mz800-ldr.mzf`.
  - Stub na $1200: režim MZ-700, hlavní část na $C000.
  - Detekce MemExt (PEHU / Lüftner / nic, s hláškou).
  - Přesun sebe i zásobníku do společné banky přes okno $4000 (kopie, pak přepnutí na stejnou adresu, mezi tím
    žádný CALL).
  - Sekvenční čtení `MZ800_std.rom` (aktuální adresář, pak `/romwbw/`) po 32 KB do bank $80–$8B, pak režim 800 a
    `JP 0`.
  - Plný `.rom` naplní i RAM disk utilitami RomWBW.
  - **Ověřeno** (`run_loader.py`): PEHU i Lüftner (náhodná RAM) až po `DIR` s utilitami, chyba bez MemExt, chyba bez
    souboru.
  - **Připraveno na 1. test na reálném HW:** návod v [test-hw.md](test-hw.md).
- **RTC z Unikarty je hotové:** `Source/HBIOS/ucrtc.asm` (modul UCRTC, `RTCDEV_UC` = $0C, `UCRTCENABLE`).
  - Čte 62h/63h (binárně), převádí na BCD `YYMMDDHHMMSS`, roky 1980–2079. Čas se čte před datem i po něm, aby
    nevadila půlnoc.
  - Nastavuje přes 60h/61h. NVRAM ani alarm karta nemá.
  - **Ověřeno** (`run_loader.py`): po startu je v `UCRTC_BUF` dnešní datum a ovladač je RTC HBIOS.
  - **ZSDOS:** `TD.COM` hlásí „NO Clock Driver“, protože ZSDOS potřebuje ovladač hodin nahraný přes `LDDS.COM` (RSX
    `wbwclk`, používá HBIOS RTC). `LDDS.COM` je na diskových obrazech RomWBW, v obrazu RAM disku není.
- **Ztracené rané hlášky:**
  - Moduly před MZV (CPU, paměť, UCRTC…) a banner HBIOS píšou do konzole dřív, než existuje, takže na obrazovce
    nejsou. Vidět je až od MZV dál.
  - **Řešení na později:** vlastní jednoduchá znaková jednotka v PREINIT MZV jako boot konzole. Po INIT se konzole
    přepne na TERM (CRTACT).
- **Vyvolání posledního řádku klávesou BLANK** (jako u Lamače) je hotové v `mzkbd.asm`.
  - **Sledování řádku:** ovladač sleduje znaky, které vrací: tisknutelné, BS/DEL, ^C ^U ^X ESC maže řádek, CR
    ukončí.
  - **Vyvolání:** BLANK na prázdném řádku vrátí uložený řádek jako by byl napsaný.
  - **Ověřeno:** `run_console.py`.
- **RAM disk Unikarty je hotový (etapa 3 uzavřena):** `Source/HBIOS/ucrd.asm` (modul UCRD, `DIODEV_UCRD` = $13,
  `UCRDENABLE`).
  - **Porty:** E9h banka, EBh adresa (`OUT (C),r`), EAh data přes INIR/OTIR.
  - **Velikost:** detekuje se aliasem bank (test bajt na $01F0 každé banky, obnovuje se).
  - **8–16 MB:** `MID_HD` s virtuálním MBR na LBA 0 (jen pro čtení, oddíl 2Eh od LBA 1, slice × 16384 sektorů),
    fyzický sektor = LBA − 1. 16 MB = 2 slice hd1k bez prefixu.
  - **4–8 MB:** `MID_RF` přes první 4 MB. Menší obrazy se nepoužijí.
  - **Jména UCRD** jsou v `devlist`, `assign` a CBIOS. CBIOS dostal i chybějící `I2CEE`.
  - **Na PC:** `mzdev/tools/diskdefs` (`mz_ucrd_0`, `mz_ucrd_1`, `mz_ucrd_rf`) pro cpmtools z `Tools/cpmtools`.
  - **Ověřeno** (`run_ucrd.py`):
    - 16 MB obraz vyplněný E5;
    - `B:=UCRD0:0`, `C:=UCRD0:1`;
    - PIP na obě slice, spuštění z RAM disku;
    - cpmtools na hostu vidí soubory.
  - **ZSDOS a PIP:** kopie pod stejným jménem, jaké je na A:, se ptá „DESTINATION IS R/O“. ZSDOS najde originál na A:
    přes cestu (path) a soubory z obrazu RAM disku mají R/O. Není to chyba ovladače.
  - **Pro uživatele:** obraz připravit jako soubor 16 MB (nebo 8 MB) a cestu zapsat do `/unicard/ramdisc.cfg`.
    - Obraz vyplněný E5 je hned prázdný disk.
    - Obraz z nul je potřeba v CP/M smazat `CLRDIR B:` a `CLRDIR C:`.
- **Etapa 4, disketový řadič DD je hotový (2026-11-06):** `Source/HBIOS/mzfd.asm` (modul MZFD, typ `DIODEV_FD`,
  jména `FD0:`…, `MZFDENABLE`).
  - **Řadič:** porty D8–DFh, příkazy, status, stopa, sektor i data se negují (CPL).
    - DCh = $84 | mechanika, DDh = strana (bit 0 = 1 je strana 1, tam je bootovací stopa IPL). DEh a DFh drží 0.
    - **Příkazy jako Lamač 4.1:** READ $82/$8A, WRITE $A2/$AA (porovnání strany, strana v bitu 3), READ ADDRESS
      $C0. SEEK $18 a RESTORE $08 s krokem `MZFDSTEP` (výchozí r=00, 6 ms v DD).
    - **Status bit 7 (NOT READY) se netestuje**, WD1772/VR177X tam hlásí motor. Chybou je RNF, CRC, LOST DATA (u
      zápisu i WP a WF) a příkaz, který skončí dřív, než prošla všechna data.
  - **Přenos dotazováním:**
    - čtení 87 T, zápis 90 T na bajt (DD má 113 T);
    - DI jen od prvního DRQ do konce sektoru (≈ 16 ms);
    - při čekání na sektor jsou mezi dotazy na status okna `EI / NOP / DI`, tik tedy nepropadne;
    - timeout ≈ 3,7 s (bez diskety nejsou indexové pulzy a řadič by čekal věčně), pak FORCE INTERRUPT.
  - **Média:** `MID_FD720` (80 válců) a `MID_FD360` (40 válců), 9 × 512 B, log. stopa = válec × 2 + strana.
    - Datová oblast Lamačových 720K a 360K je stejná, Lamač u 360K jen používá na adresář 2 ze 4 bloků, které
      `DPB_FD360` rezervuje. Disky jsou tedy oboustranně kompatibilní.
    - **Detekce:** RESTORE, válec 2, READ ADDRESS. Formát dává typ mechaniky (`MZFDnTYPE`). V 5,25" mechanice
      s 80 stopami (`FDT_5HD`) znamená válec 1 v ID disketu se 40 stopami, ta se pak čte dvojitým krokem.
  - **Motor:** start 500 ms (`MZFDSPIN`), usazení hlavy 15 ms (`MZFDSETL`), vypnutí 3 s po posledním přístupu
    z tiku (`MZFDMOTO`, háček `VEC_TICK`).
  - **5 pokusů** na sektor, od třetího s rekalibrací. Pak `MZFD0: ERR ST=.. C=.. H=.. S=..` a `ERR_IO`.
  - **Nástroj:** `mzdev/tools/mzdsk.py` vytvoří DSK 720/360 (`--lamac` s bootovací stopou 16 × 256 B), převede ho
    na surový obraz pro cpmtools (`wbw_fd720`, `wbw_fd360`) a zpět. Snese poškozenou tabulku velikostí stop.
  - **Ověřeno** (`run_fd.py`):
    - Lamačova disketa s programy (kopie `Martin-MZ-FDC/work/emu/prg41.dsk`) jako `B:`, DIR ukáže všechny
      soubory;
    - PIP dvou souborů na prázdnou disketu `C:`, program z ní běží;
    - po konci emulátoru cpmtools z DSK vytáhnou kopie a ty se shodují s originály;
    - motor se po 3 s vypne.
  - **Ručně ověřeno:** 360K s bootovací stopou Lamače na `FDT_5DD` (dočasná konfigurace), STAT ukazuje 342 KB, kopie
    na PC sedí.
  - **Lamačovy obrazy DSK:** systémová disketa 4.1 má prázdný adresář. Obraz s programy
    (`MFDC800T/DSK/CPMv41 Prg CPM.dsk`) má poškozenou hlavičku (stopa 46/0 hlásí 79/0, dvě stopy chybí), soubory na
    nižších válcích jsou ale v pořádku.
- **Etapa 5, boot z diskety (2026-11-06):**
  - **Zavaděč IPL** `Source/MZ800/mzipl.asm` → `Binary/mz800-ipl.bin` (4096 B = bootovací stopa).
    - **Hlavička IPLPRO:** jméno „ROMWBW“, velikost, načtení i start na $1200, první logický sektor 1.
    - **Za skokem na $1200 jsou parametry:** „RWB“, formát (0 = 720K, 1 = 360K), dvojitý krok, jméno souboru
      (11 B jako v adresáři).
    - **Zavaděč** přepne do režimu MZ-700, detekuje MemExt a přesune se do společné banky.
    - Přečte adresář CP/M z mechaniky 0 a nahraje soubor `ROMWBW.ROM` (uživatel 0) po extentech a blocích do bank
      $80…, nejvýš 12. Pak spustí HBIOS.
    - **Čtení dotazováním** jako v `mzfd.asm`. 5 pokusů, chyba se vypíše s C/H/S a statusem.
    - **Společný kód** se zavaděčem z Unikarty je v `Source/MZ800/mzcommon.asm` (MemExt, přesun, text, start
      HBIOS).
  - **Rozložení MZ v `mzfd.asm`:** detekce čte ID na válci 0 / straně 1. N = 1 (256 B) znamená disketu Lamače
    (`MZFD_MZL`).
    - Rezervované stopy se pak mapují: log. 0 = válec 0 / strana 0, 1 = válec 1 / 0, 2 = válec 1 / 1.
    - **Log. stopa 3 = bootovací stopa:** sektor S (0–7) jsou její sektory 2S+1 a 2S+2 po 256 B, bez CPL a bez
      porovnání strany. Je to přesně pohled ROM, takže MZSYS zapisuje IPL přes HBIOS.
    - Prvních 27 sektorů (`zsys_wbw.sys` má přesně 13 824 B) tak bootovací stopu nezasáhne a romldr i SYSCOPY
      fungují beze změny. Datová oblast se nemění.
  - **`MZSYS.COM`** (`Source/MZ800/mzsys.asm` → `Binary/Apps/mzsys.com`, obraz IPL je vložený `#INCLUDE`):
    - `MZSYS D: [JMENO.EXT]`;
    - kontroluje RomWBW (`HB_IDENT` na $FFFC), CP/M 2.2 a DPB (SPT 36, DSM 350 nebo 170);
    - rozložení MZ pozná tak, že stopa 3 má 1. sektor, ale ne 9.;
    - zapíše 32 záznamů na stopu 3 přes BIOS, jako SYSCOPY.
  - **`mzdsk.py mkboot`:** bootovací DSK (IPL, `ROMWBW.ROM`, volitelně systém do rezervovaných stop a další
    soubory přes cpmtools).
  - **Ověřeno** (`run_ipl.py`):
    - reset s bootovací disketou: zavaděč IPL, 12 bank, menu romldr;
    - `1` (FD0) nabootuje ZSDOS z rezervovaných stop, `A:=FD0:0`;
    - MZSYS odmítne disketu bez bootovací stopy MZ a zapíše IPL na prázdnou disketu v rozložení MZ.
  - **Rychlost:** zavaděč čte sektory po jednom v logickém pořadí. Při prokládání 2:1 to jsou asi 2 otáčky na stopu,
    tedy kolem 11 KB/s. `.rom` (384 KB) se bude na reálném HW číst asi 35 s, `.upd` (128 KB) asi 12 s. Zrychlit
    se dá čtením celé stopy v pořadí na disku.
- **Formátování (etapa 5):**
  - **DIODEFMED v `mzfd.asm`:** E = `MID_FD720` nebo `MID_FD360`, bit 7 E = rozložení MZ (rozšíření pro MZ-800).
    Nastaví médium bez detekce. 360K v 5,25" mechanice s 80 stopami dostane dvojitý krok.
  - **DIOFORMAT** (D = strana, E = výplň, HL = válec) zapíše stopu příkazem WRITE TRACK ($F0).
    - **Stopa jako seznam běhů (počet, bajt) v `HB_WRKBUF`**, bajty už negované, počet 0 = 256:
      - GAP 4a 80 × 4E, IAM, GAP 1 50 × 4E;
      - za každý sektor ID a datové pole, GAP 3 84 (9 × 512) nebo 50 (16 × 256);
      - nakonec 1024 × 4E až do indexu.
    - **Smyčka:** 66 T na bajt, na konci běhu 99 T (DD má 113 T). Přerušení jsou zakázaná po celou stopu.
    - **Prokládání:** 9 × 512 jako Lamačův FORMAT4 (1,6,2,7,3,8,4,9,5). V rozložení MZ dostane válec 0 / strana
      1 bootovací stopu 16 × 256 po sobě.
  - **`MZFMT.COM`** (`Source/MZ800/mzfmt.asm` → `Binary/Apps/mzfmt.com`): `MZFMT D: [/360] [/PC]`.
    - Jednotku HBIOS najde přes mapu jednotek CBIOS (`$44` → CBX → `DRVMAPADR`) a ověří, že jde o disketu MZ-800
      (`DIODEV_FD`, I/O $D8).
    - Výchozí je 720K v rozložení MZ, `/360` (výchozí v 5,25" DD) a `/PC` bez bootovací stopy.
    - Po potvrzení Y zavolá DEFMED a DIOFORMAT pro všechny stopy, pak reset disků BDOS.
- **Oprava konzole (2026-11-07):** HBIOS při každém skoku na 0 (konec programu, teplý start) volá `TERM_RESET`,
  a ten volá VDARES. `MZV_VDARES` dřív smazal obrazovku a vrátil kurzor domů, takže po každém programu zůstal jen
  prompt.
  - Teď VDARES jen znovu nastaví registry GDG a posun obrazu a obsah nechá (jako `TMS_VDARES`).
  - Plná inicializace se smazáním je ve VDAINI (start, `TERM_ATTACH`).
- **Etapa 6, HD diskety (2026-11-07):** `MZFDHD` (HD úprava řadiče, v `cfg_MZ800.asm` zapnutá).
  - **Přenos HD přes přerušení od DRQ** jako u Lamače:
    - DFh = 1, DEh = 1 (HD) jen na dobu příkazu, krokuje se v DD;
    - IM 1 se 7bajtovou obsluhou na $0038 banky HBIOS (uloží se a vrátí): čtení `IN / CPL / LD (HL),A / INC HL / EI
      / RET`, zápis `OUT / INC HL / LD A,(HL) / CPL / EI / RET`;
    - čekací smyčka `IN B,(C) / RRC B / JP C` nepoužívá A ani HL a má timeout ≈ 1 s (`DEC DE / INC D / DEC D`);
    - během příkazu je vypnuté přerušení PIO A (tik VBLN), tiky se ztrácejí; potom IM 2 a PIO zpět;
    - počet přenesených bajtů se kontroluje (HL obsluhy proti očekávaným 512).
  - **Detekce** v mechanice HD (`FDT_3HD`, `FDT_5HD`): READ ADDRESS na válci 2 v HD, pak čtení posledního sektoru
    (18 nebo 15). Když neprojde, je disketa DD.
  - **Média:**
    - RomWBW `MID_FD144`, `MID_FD120`;
    - **nově `MID_MZ144` (11) a `MID_MZ120` (12)** pro Lamačovy HD formáty (bloky 4K, 256 položek, 4 rezervované
      stopy), poznají se podle bootovací stopy MZ;
    - DPB jsou v `hbios.inc`, `ubios.inc`, CBIOS (`DPBMAP`) a CP/M 3 (`diskio.z80`, `biosldr.z80`).
  - **Na Lamačových HD disketách je DD jen bootovací stopa** (válec 0 / strana 1), ostatní stopy včetně
    rezervovaných jsou HD 18 × 512 (`Martin144.dsk`, FORMAT4). Mapa rezervovaných stop z etapy 5 platí beze změny.
  - **Ověřeno** (`run_hd.py`, kopie `Martin144.dsk`):
    - STAT 1404K, 32 záznamů na blok, 72 sektorů na stopu, 4 rezervované;
    - DIR, COPY dvou souborů s ověřením;
    - tik dál běží;
    - cpmtools (`mz_lamac144` v `mzdev/tools/diskdefs`) přečtou kopie shodné s originály.
  - **Formátování HD zatím není:** WRITE TRACK v HD potřebuje přerušení i pro proud běhů. DIOFORMAT hlásí
    `ERR_NOTIMPL`. HD diskety formátovat v Lamačově CP/M (FORMAT4).
- **Zavaděč IPL pro HD (rozpracováno):** formáty 2 (1,44M) a 3 (1,2M) v `FMTTBL` (sektory na stopu, bloky 4K,
  adresář 16 sektorů, 16bitová čísla bloků, EXM 1). Sektory HD čte přes přerušení do `BOUNCE` ($A000). $0038
  leží v nahrávané bance, proto se po každém sektoru obnoví. MZSYS pozná formát z DPB.
- **Další krok:** ověřit boot z HD diskety v emulátoru, pak etapa 7 (CP/M 3/ZPM3, UC.COM, dokumentace).

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
  - RAM disk Unikarty zastupuje MZ-1R18 SRAM 16M na stejných portech;
  - **past:** s `runtime_check_on_connect = 1` (výchozí) se Unicard nepřipojí, když v SD kořeni chybí runtime Manageru
    (`unicard/`). Čeká na dialog a porty 50h/51h čtou $FB. Harness proto kontrolu vypíná;
  - SD kořen testů je `mzdev/work/sd`.
- **TASM vyhodnocuje výrazy zleva doprava bez priority operátorů:** `A > B + C` je `(A > B) + C`. Závorkovat.

## Testy

- `python mzdev/tests/emu/run_memext.py`: MemExt PEHU/Lüftner/žádný, 512 KB přes harness, párování stránek PEHU.
- `python mzdev/tests/emu/run_hbios.py`: `Binary/MZ800_std.upd` přímo do MemExt, start HBIOS (PEHU, Lüftner, bez
  MemExt). Předpokládá hotový build `MZ800 std`.
- `python mzdev/tests/emu/run_console.py [PEHU|LUFTNER] [--random]`: konzole a klávesnice, boot ZSDOS, DIR, scroll.
  Text obrazovky čte `mzdev/tools/emu/vramtext.py` (glyfy z `Source/Fonts/font8x8u.bin`).
- `python mzdev/tests/emu/run_loader.py`: zavaděč MZF z emulované Unikarty až po ZSDOS a `DIR` (PEHU, Lüftner, bez
  MemExt, bez souboru). Předpokládá build `MZ800 std` a `Source\BuildMZ800.cmd`.
- `python mzdev/tests/emu/run_ucrd.py`: RAM disk Unikarty 16 MB, PIP na obě slice, kontrola cpmtools.
- `python mzdev/tests/emu/run_fd.py`: diskety DD, čtení Lamačovy diskety, zápis, kontrola cpmtools, vypnutí motoru.
- `python mzdev/tests/emu/run_ipl.py`: boot z diskety (IPL, romldr z FD0), MZSYS, nová bootovací disketa (asi
  15 min). Předpokládá build `MZ800 std` a `Source\BuildMZ800.cmd`.
- `python mzdev/tests/emu/run_fmt.py`: MZFMT v rozložení MZ i PC, kontrola stop v DSK a souboru přes cpmtools.
- `python mzdev/tests/emu/run_hd.py`: HD 1,44M Lamače (přerušení od DRQ), STAT, DIR, COPY, tik, cpmtools.
- **Symboly:** TASM nedělá soubor symbolů. `mzdev/tools/emu/tasmlst.py` vytáhne adresy návěští z `.lst`, např.
  `Source/HBIOS/hbios_rom.lst`, `romldr.lst`.
- **Proměnné HBIOS** číst přes `memext_read` z banky $80 (offset 0), ne přes pohled CPU. Ten ukazuje banku, která
  je zrovna namapovaná.

## Pasti

- **Git Bash a Python s heredocem:** úprava `Makefile` přes `python -I - <<EOF` nenašla řetězec, který tam je.
  Úpravy souborů se CRLF dělat skriptem spuštěným z PowerShellu.
  - `'\n'` v heredocu se do souboru zapíše jako skutečný konec řádku. Řetězce s `\n` upravovat nástrojem Edit.
  - `sed -i` v Git Bash odstraní CR z celého souboru.
- **Emulátor a FDC:** stopu v DSK vybírá podle registru stopy, ne podle polohy hlavy. READ ADDRESS vrací jako válec
  registr stopy. Dvojitý krok se v něm tedy vyzkoušet nedá.
- **Lamačův DUMP** otevírá soubor jen na aktuální jednotce (`c:` a pak `ldump ldump.com`).
- **PIP a cesta ZSDOS:** když soubor s cílovým jménem leží na jednotce v cestě (A:), PIP selže.
  - Je-li ten soubor R/O, PIP se ptá „DESTINATION IS R/O“.
  - Je-li R/W, PIP skončí bez hlášky a kopie zůstane jako `.$$$` (ZSDOS najde soubor na A: při přejmenování).
  - **Řešení:** cílové jméno, které na A: není, nebo ZSDOS `COPY` (umí i ověření).
- **Emulátor a `fdd_storage='cached'`:** při ukončení zapíše obraz zpět a umí přitom poškodit hlavičku DSK
  (bootovací disketa se pak v dalším běhu nenačte celá). `cached` jen pro mechaniky, do kterých test opravdu
  zapisuje: `Emu(fdd_storage={1: 'cached'})`.
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
