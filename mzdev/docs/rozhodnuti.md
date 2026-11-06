# Rozhodnutí

Rozhodnutí autora a technická rozhodnutí s důvody. Nová dopisovat na konec, s datem.

## 2026-11-06: založení projektu

### MemExt je povinný (autor)

- **Proč:** HBIOS RomWBW potřebuje aspoň 128 KB RAM, přepínané po 32 KB pod pevnou horní 32 KB (`std.asm`,
  `SystemGuide.md`). Režim bez bank v RomWBW není (`MM_NONE` je jen symbol bez kódu).
- **Základní MZ-800 nestačí:** má 64 KB a porty E0–E6 jen překrývají ROM, CG-ROM a VRAM, paměť navíc nepřidají.
- **Zamítnuté varianty:**
  - **HBIOS bez bank:** TPA by kleslo na odhadem 40–44K.
  - **Vlastní kompaktní BIOS pro 64 KB:** TPA kolem 52K, ale to už není RomWBW a jeho utility by nefungovaly.
- **Výsledek:** TPA 54K (CP/M 2.2/ZSDOS) a 60K (CP/M 3/ZPM3). Lamač 4.1 má ≈ 55K.

### PEHU i Lüftner s detekcí za běhu (autor)

- Autor má PEHU, ale port má fungovat s oběma deskami. Bez MemExt zavaděč vypíše chybovou hlášku.
- **Detekce:** stránka 4 (4000h) na dvě různé banky se značkami. Pak zápis jen na lichou stránku 5:
  - PEHU zarovná zápis na pár 4–5, takže se změní i 4000h;
  - Lüftner stránku 4 nechá.
- Ověřeno proti modelu v emulátoru: `mzdev/tests/emu/run_memext.py`.
- **Plán bank je pro obě desky stejný** (16 bank RomWBW po 32 KB). Liší se jen rutina bank select v proxy:
  - PEHU: 4 OUTy po 8 KB;
  - Lüftner: 8 OUTů po 4 KB.
- HBIOS si při initu nakopíruje variantu podle typu, který mu předá zavaděč.

### Formáty disket: Lamač i RomWBW (autor)

- **Formáty Lamače (CP/M 1.4/4.1):** 360K, 720K, 1.2M, 1.44M, datově kompatibilní, čtení i zápis jeho disket.
  Bootovací stopa 16×256 na válci 0 / straně 1.
- **Standardní formáty RomWBW** (FD720, FD144, FD360, FD120) pro výměnu disket s jinými stroji.
- Rozložení se pozná podle velikosti sektoru na válci 0 / straně 1: 256 B = MZ/Lamač, 512 B = RomWBW/PC.
- DPB 720K je u obou shodný, 360K se liší jen v AL0 (RomWBW F0h, Lamač C0h), 1.2M/1.44M Lamače potřebují nová MID.

### Repo: fork RomWBW s cílem upstream (autor)

- **Repo:** klon `wwarthen/RomWBW`, větev `mz800`, remote `upstream`. Fork na GitHubu se založí, až o to autor řekne.
- **Kód platformy** v konvencích RomWBW (TASM, CRLF, `cfg_MZ800.asm`, `Config/MZ800_*.asm`, `Source/MZ800/`), aby šel
  nabídnout jako PR.
- **Vývojové věci jsou v `mzdev/`** (česká dokumentace, Python, testy) a v `CLAUDE.md`. Do PR nepatří.

### Soubory ze SD karty: nejdřív utilita (technické)

- Unicard fw 0.26 má rozbitý SEEK, a v API je jen jeden otevřený soubor a jeden adresář. Skutečný disk CP/M nad
  soubory SD by musel náhodný přístup simulovat znovuotevřením a přeskočením.
- Proto nejdřív `UC.COM` (DIR/GET/PUT, sekvenčně) a disk až jako bonus na konci.
- Přenos PC ↔ CP/M zajistí i obraz RAM disku Unikarty, protože je to surový soubor na SD (cpmtools).

### RAM disk Unikarty jako hd1k (technické)

- Ovladač vytvoří virtuální MBR na LBA 0 s oddílem 2Eh od LBA 1. Obraz 16 MB tak obsahuje přesně dvě standardní
  slice hd1k, bez prefixu.
- **Na PC:** cpmtools s `wbw_hd1k` a offsetem 0 / 8M.
- **4 MB obraz:** jako `MID_RF`. Menší obrazy se odmítnou.
