@echo off
setlocal

::
:: Build SHARP MZ-800 loaders (Unicard MZF, floppy IPL boot track)
::

set TOOLS=../../Tools

set PATH=%TOOLS%\tasm32;%PATH%

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
