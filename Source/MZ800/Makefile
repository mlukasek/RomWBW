OBJECTS = mz800-ldr.mzf mz800-ipl.bin mzsys.com mzfmt.com uc.com mzramdsk.bin
NOCOPY = mzramdsk.bin
DEST = ../../Binary
TOOLS = ../../Tools
include $(TOOLS)/Makefile.inc

mz800-ldr.mzf: mzfldr.asm mzcommon.asm
	$(TASM) $< $@ mzfldr.lst
	cp mz800-ldr.mzf $(DEST)/mz800-ldr.mzf

mz800-ipl.bin: mzipl.asm mzcommon.asm
	$(TASM) $< $@ mzipl.lst
	cp mz800-ipl.bin $(DEST)/mz800-ipl.bin

mzsys.com: mzsys.asm mzipl.asm mzcommon.asm
	$(TASM) $< $@ mzsys.lst
	cp mzsys.com $(DEST)/Apps/mzsys.com

mzfmt.com: mzfmt.asm
	$(TASM) $< $@ mzfmt.lst
	cp mzfmt.com $(DEST)/Apps/mzfmt.com

uc.com: uc.asm
	$(TASM) $< $@ uc.lst
	cp uc.com $(DEST)/Apps/uc.com

# RAM disk A: of the MZ-800 (256K in MemExt, loaded from the .rom image): the standard ROM disk contents without
# the tools for other hardware (FDU: 765 floppy controllers, FLASH: flash ROM, RTC: DS1302), plus the MZ-800
# utilities and WDATE (date and time through HBIOS). The .rom images made by the HBIOS build are put together
# again with it. cpmtools read the disk formats from the diskdefs file in the current directory, so they run
# in ../RomDsk.
mzramdsk.bin: ../RomDsk/rom256_wbw.dat uc.com mzsys.com mzfmt.com
	cp $< $@
	cd ../RomDsk && $(BINDIR)/cpmrm -f wbw_rom256 ../MZ800/$@ 0:fdu.com 0:flash.com 0:rtc.com
	cd ../RomDsk && $(CPMCP) -f wbw_rom256 ../MZ800/$@ ../MZ800/uc.com ../MZ800/mzsys.com ../MZ800/mzfmt.com \
		../Images/Common/All/u15/WDATE.COM 0:
	cd ../RomDsk && $(CPMCHATTR) -f wbw_rom256 ../MZ800/$@ r 0:*.*
	for f in $(DEST)/MZ800_*.upd ; do [ -f "$$f" ] && cat "$$f" $@ > "$${f%.upd}.rom" ; done ; true
