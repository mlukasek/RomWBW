@echo off
setlocal

::
:: Build SHARP MZ-800 loader (Unicard MZF)
::

set TOOLS=../../Tools

set PATH=%TOOLS%\tasm32;%PATH%

set TASMTABS=%TOOLS%\tasm32

tasm -t80 -g3 mzfldr.asm mz800-ldr.mzf mzfldr.lst || exit /b

if exist mz800-ldr.mzf copy mz800-ldr.mzf ..\..\Binary\ || exit /b
