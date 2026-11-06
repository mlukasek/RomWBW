OBJECTS = mz800-ldr.mzf
DEST = ../../Binary
TOOLS = ../../Tools
include $(TOOLS)/Makefile.inc

mz800-ldr.mzf: mzfldr.asm
	$(TASM) $< $@ mzfldr.lst
	cp mz800-ldr.mzf $(DEST)/mz800-ldr.mzf
