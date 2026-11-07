@echo off
setlocal

::
:: Build SHARP MZ-800 loaders (Unicard MZF, floppy IPL boot track)
::

set TOOLS=../../Tools

set PATH=%TOOLS%\tasm32;%TOOLS%\cpmtools;%PATH%

set TASMTABS=%TOOLS%\tasm32

tasm -t80 -g3 mzfldr.asm mz800-ldr.mzf mzfldr.lst || exit /b

if exist mz800-ldr.mzf copy mz800-ldr.mzf ..\..\Binary\ || exit /b

tasm -t80 -g3 mzipl.asm mz800-ipl.bin mzipl.lst || exit /b

if exist mz800-ipl.bin copy mz800-ipl.bin ..\..\Binary\ || exit /b

tasm -t80 -g3 mzsys.asm mzsys.com mzsys.lst || exit /b

if exist mzsys.com copy mzsys.com ..\..\Binary\Apps\ || exit /b

tasm -t80 -g3 mzfmt.asm mzfmt.com mzfmt.lst || exit /b

if exist mzfmt.com copy mzfmt.com ..\..\Binary\Apps\ || exit /b

tasm -t80 -g3 uc.asm uc.com uc.lst || exit /b

if exist uc.com copy uc.com ..\..\Binary\Apps\ || exit /b

::
:: RAM disk A: of the MZ-800 (256K in MemExt, loaded from the .rom image):
:: the standard ROM disk contents without the tools for other hardware
:: (FDU: 765 floppy controllers, FLASH: flash ROM, RTC: DS1302), plus the
:: MZ-800 utilities and WDATE (date and time through HBIOS).
:: The .rom images made by the HBIOS build are put together again with it.
:: cpmtools read the disk formats from the diskdefs file in the current
:: directory, so they run in ..\RomDsk.
::

copy /b ..\RomDsk\rom256_wbw.dat mzramdsk.bin || exit /b
pushd ..\RomDsk
cpmrm -f wbw_rom256 ../MZ800/mzramdsk.bin 0:fdu.com 0:flash.com 0:rtc.com || exit /b
cpmcp -f wbw_rom256 ../MZ800/mzramdsk.bin ../MZ800/uc.com ../MZ800/mzsys.com ../MZ800/mzfmt.com ../Images/Common/All/u15/WDATE.COM 0: || exit /b
cpmchattr -f wbw_rom256 ../MZ800/mzramdsk.bin r 0:*.* || exit /b
popd

for %%f in (..\..\Binary\MZ800_*.upd) do copy /b %%f + mzramdsk.bin ..\..\Binary\%%~nf.rom || exit /b
