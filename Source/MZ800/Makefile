OBJECTS = mz800-ldr.mzf mz800-ipl.bin mzsys.com mzfmt.com
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
