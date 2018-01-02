; The purpose of this file is to define generic symbols and to include
; the appropriate std-*.inc file to bring in platform specifics.

; There are several classes of systems supported by SBC.
; 1. SBC 	Z80 SBC (v1 or v2) w/ ECB interface
; 2. ZETA	Standalone Z80 SBC w/ SBC compatibility
; 3. ZETA2	Second version of ZETA with enhanced memory bank switching
; 4. N8		MSX-compatible Z180 SBC w/ onboard video and sound
; 5. MK4	Mark IV Z180 based SBC w/ ECB interface
; 6. UNA	Any Z80/Z180 computer with UNA BIOS
; 7. RC		RC2014 based system with SMB 512K RAM/ROM card

; All the classes require certain generic definitions, and these are
; defined here prior to the inclusion of platform specific .inc files.

; It is unfortunate, but all the possible config items must be defined
; here because the config gets read before the specific std-*.inc's

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; INCLUDE VERSION
;
#INCLUDE "ver.inc"			; ADD BIOSVER
;
FALSE		.EQU 	0
TRUE		.EQU 	~FALSE
;
; PRIMARY HARDWARE PLATFORMS
;
PLT_SBC		.EQU	1		; SBC ECB Z80 SBC
PLT_ZETA	.EQU	2		; ZETA Z80 SBC
PLT_ZETA2	.EQU	3		; ZETA Z80 V2 SBC
PLT_N8		.EQU	4		; N8 (HOME COMPUTER) Z180 SBC
PLT_MK4		.EQU	5		; MARK IV
PLT_UNA		.EQU	6		; UNA BIOS
PLT_RC		.EQU	7		; RC2014
;
#IF (PLATFORM != PLT_UNA)
#INCLUDE "hbios.inc"
#ENDIF
;
; BOOT STYLE
;
BT_MENU		.EQU	1		; WAIT FOR MENU SELECTION AT LOADER PROMPT
BT_AUTO		.EQU	2		; AUTO SELECT BOOT_DEFAULT AFTER BOOT_TIMEOUT
;
; FLOPPY DISK MEDIA SELECTIONS (ID'S MUST BE INDEX OF ENTRY IN FCD_TBL)
;
FDM720		.EQU	0		; 3.5" FLOPPY, 720KB, 2 SIDES, 80 TRKS, 9 SECTORS
FDM144		.EQU	1		; 3.5" FLOPPY, 1.44MB, 2 SIDES, 80 TRKS, 18 SECTORS
FDM360		.EQU	2		; 5.25" FLOPPY, 360KB, 2 SIDES, 40 TRKS, 9 SECTORS
FDM120		.EQU	3		; 5.25" FLOPPY, 1.2MB, 2 SIDES, 80 TRKS, 15 SECTORS
FDM111		.EQU	4		; 8" FLOPPY, 1.11MB, 2 SIDES, 74 TRKS, 15 SECTORS
;
; MEDIA ID VALUES
;
MID_NONE	.EQU	0
MID_MDROM	.EQU	1
MID_MDRAM	.EQU	2
MID_RF		.EQU	3
MID_HD		.EQU	4
MID_FD720	.EQU	5
MID_FD144	.EQU	6
MID_FD360	.EQU	7
MID_FD120	.EQU	8
MID_FD111	.EQU	9
;
; DS RTC MODE SELECTIONS
;
DSRTCMODE_NONE	.EQU	0		; NO DSRTC
DSRTCMODE_STD	.EQU	1		; ORIGINAL DSRTC CIRCUIT (SBC, ZETA, MK4)
DSRTCMODE_MFPIC	.EQU	2		; MF/PIC VARIANT
;
; SIO MODE SELECTIONS
;
SIOMODE_NONE	.EQU	0
SIOMODE_RC	.EQU	1		; RC2014 SIO MODULE FROM SPENCER
SIOMODE_SMB	.EQU	2		; RC2014 SIO MODULE BY SCOTT BAKER
;
; FD MODE SELECTIONS
;
FDMODE_NONE	.EQU	0
FDMODE_DIO	.EQU	1		; DISKIO V1
FDMODE_ZETA	.EQU	2		; ZETA
FDMODE_ZETA2	.EQU	3		; ZETA V2
FDMODE_DIDE	.EQU	4		; DUAL IDE
FDMODE_N8	.EQU	5		; N8
FDMODE_DIO3	.EQU	6		; DISKIO V3
FDMODE_SMBSMC	.EQU	7		; RC2014 SMB SMC9266
FDMODE_SMBWDC	.EQU	8		; RC2014 SMB WD37C65

;
; IDE MODE SELECTIONS
;
IDEMODE_NONE	.EQU	0
IDEMODE_DIO	.EQU	1		; DISKIO V1
IDEMODE_DIDE	.EQU	2		; DUAL IDE
IDEMODE_MK4	.EQU	3		; MARK IV ONBOARD IDE (8 BIT)
IDEMODE_RC	.EQU	4		; RC2014 CF BOARD (8 BIT)
IDEMODE_SMB	.EQU	5		; RC2014 IDE SMB $E0 IO BASE (8 BIT)
;
; PPIDE MODE SELECTIONS
;
PPIDEMODE_NONE	.EQU	0
PPIDEMODE_SBC	.EQU	1		; STANDARD SBC PARALLEL PORT
PPIDEMODE_DIO3	.EQU	2		; DISKIO V3 PARALLEL PORT
PPIDEMODE_MFP	.EQU	3		; MULTIFUNCTION / PIC
PPIDEMODE_N8	.EQU	4		; MULTIFUNCTION / PIC
PPIDEMODE_RC	.EQU	5		; RC2014 PPIDE STANDARD $20 IO BASE
;
; SD MODE SELECTIONS
;
SDMODE_NONE	.EQU	0
SDMODE_JUHA	.EQU	1		; JUHA MINI BOARD
SDMODE_N8	.EQU	2		; N8-2511, UNMODIFIED
SDMODE_CSIO	.EQU	3		; N8-2312 OR N8-2511 MODIFIED
SDMODE_PPI	.EQU	4		; PPISD MINI BOARD
SDMODE_UART	.EQU	5		; SD INTERFACE VIA UART
SDMODE_DSD	.EQU	6		; DUAL SD
SDMODE_MK4	.EQU	7		; MARK IV
;
; SERIAL DEVICE CONFIGURATION CONSTANTS
;
SER_DATA5	.EQU	0 << 0
SER_DATA6	.EQU	1 << 0
SER_DATA7	.EQU	2 << 0
SER_DATA8	.EQU	3 << 0
;
SER_PARNONE	.EQU	0 << 3
SER_PARODD	.EQU	1 << 3
SER_PAREVEN	.EQU	3 << 3
SER_PARMARK	.EQU	5 << 3
SER_PARSPACE	.EQU	7 << 3
;
SER_STOP1	.EQU	0 << 2
SER_STOP2	.EQU	1 << 2
;
; SERIAL BAUD RATES ENCODED AS V = 75 * 2^X * 3^Y
; AND STORED AS 5 BITS: YXXXX
;
SER_BAUD300	.EQU	$02 << 8
SER_BAUD600	.EQU	$03 << 8
SER_BAUD1200	.EQU	$04 << 8
SER_BAUD2400	.EQU	$05 << 8
SER_BAUD4800	.EQU	$06 << 8
SER_BAUD9600	.EQU	$07 << 8
SER_BAUD19200	.EQU	$08 << 8
SER_BAUD38400	.EQU	$09 << 8
SER_BAUD76800	.EQU	$0A << 8
SER_BAUD115200	.EQU	$19 << 8
SER_BAUD230400	.EQU	$1A << 8
SER_BAUD460800	.EQU	$1B << 8
;
SER_XON		.EQU	1 << 6
SER_DTR		.EQU	1 << 7
SER_RTS		.EQU	1 << 13
;
SER_300_8N1	.EQU	SER_BAUD300 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_600_8N1	.EQU	SER_BAUD600 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_1200_8N1	.EQU	SER_BAUD1200 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_2400_8N1	.EQU	SER_BAUD2400 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_4800_8N1	.EQU	SER_BAUD4800 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_9600_8N1	.EQU	SER_BAUD9600 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_19200_8N1	.EQU	SER_BAUD19200 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_38400_8N1	.EQU	SER_BAUD38400 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_76800_8N1	.EQU	SER_BAUD76800 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_115200_8N1	.EQU	SER_BAUD115200 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_230400_8N1	.EQU	SER_BAUD230400 | SER_DATA8 | SER_PARNONE | SER_STOP1
SER_460800_8N1	.EQU	SER_BAUD460800 | SER_DATA8 | SER_PARNONE | SER_STOP1
;
; INTERRUPT TYPE OPTIONS
;
IT_NONE		.EQU	0
IT_SIMH		.EQU	1
IT_Z180		.EQU	2
IT_CTC		.EQU	3
IT_RC		.EQU	4
;
; INTERRUPT VECTOR TABLE ENTRY OFFSETS (Z180 COMPATIBLE)
;
IVT_INT1	.EQU	0
IVT_INT2	.EQU	2
IVT_TIM0	.EQU	4
IVT_TIM1	.EQU	6
IVT_DMA0	.EQU	8
IVT_DMA1	.EQU	10
IVT_CSIO	.EQU	12
IVT_SER0	.EQU	14
IVT_SER1	.EQU	16
;
#INCLUDE "build.inc"			; INCLUDE USER CONFIG, ADD VARIANT, TIMESTAMP, & ROMSIZE
;
#IF ((PLATFORM == PLT_N8) | (PLATFORM == PLT_MK4))
#DEFINE CPU_Z180
#ELSE
#DEFINE CPU_Z80
#ENDIF
;
; SET PLATFORM NAME STRING
;
#IF (PLATFORM == PLT_SBC)
  #DEFINE 	PLATFORM_NAME	"SBC Z80"
#ENDIF
#IF (PLATFORM == PLT_ZETA)
  #DEFINE 	PLATFORM_NAME	"ZETA Z80"
#ENDIF
#IF (PLATFORM == PLT_ZETA2)
  #DEFINE 	PLATFORM_NAME	"ZETA Z80 V2"
#ENDIF
#IF (PLATFORM == PLT_N8)
  #DEFINE 	PLATFORM_NAME	"N8 Z180"
#ENDIF
#IF (PLATFORM == PLT_MK4)
  #DEFINE 	PLATFORM_NAME	"MARK IV Z180"
#ENDIF
#IF (PLATFORM == PLT_UNA)
  #DEFINE	PLATFORM_NAME	"UNA"
#ENDIF
#IF (PLATFORM == PLT_RC)
  #DEFINE	PLATFORM_NAME	"RC2014"
#ENDIF
;
; INCLUDE PLATFORM SPECIFIC HARDWARE DEFINITIONS
;
#IF ((PLATFORM == PLT_SBC) | (PLATFORM == PLT_ZETA) | (PLATFORM == PLT_ZETA2))
#INCLUDE "plt_sbc.inc"
#ENDIF
;
#IF (PLATFORM == PLT_N8)
#INCLUDE "plt_n8.inc"
#ENDIF
;
#IF (PLATFORM == PLT_MK4)
#INCLUDE "plt_mk4.inc"
#ENDIF
;
#IF (PLATFORM == PLT_UNA)
#INCLUDE "plt_una.inc"
#ENDIF
;
#IF (PLATFORM == PLT_RC)
#INCLUDE "plt_rc.inc"
#ENDIF
;
; SETUP DEFAULT CPU SPEED VALUES
;
CPUKHZ	.EQU	CPUOSC / 1000	; CPU FREQ IN KHZ
;
#IFDEF CPU_Z180
#IF (Z180_CLKDIV == 0)
CPUKHZ	.SET	CPUKHZ / 2	; ADJUST FOR HALF SPEED OPERATION
#ENDIF
#IF (Z180_CLKDIV == 2)
CPUKHZ	.SET	CPUKHZ * 2	; ADJUST FOR DOUBLE SPEED OPERATION
#ENDIF
#ENDIF
;
CPUMHZ	.EQU	CPUKHZ / 1000	; CPU FREQ IN MHZ
;
; MEMORY BANK CONFIGURATION
;
#IF (PLATFORM == PLT_UNA)
BID_ROM0	.EQU	$0000
BID_RAM0	.EQU	$8000
#ELSE
BID_ROM0	.EQU	$00
BID_RAM0	.EQU	$80
#ENDIF

BID_ROMN	.EQU	(BID_ROM0 + ((ROMSIZE / 32) - 1))
BID_RAMN	.EQU	(BID_RAM0 + ((RAMSIZE / 32) - 1))

BID_BOOT	.EQU	BID_ROM0	; BOOT BANK
;BID_BIOSIMG	.EQU	BID_ROM0 + 1	; BIOS IMAGE BANK
BID_OSIMG	.EQU	BID_ROM0 + 2	; ROM LOADER AND IMAGES BANK
BID_FSFAT	.EQU	BID_ROM0 + 3	; FAT FILESYSTEM DRIVER BANK
BID_ROMD0	.EQU	BID_ROM0 + 4	; FIRST ROM DRIVE BANK
BID_ROMDN	.EQU	BID_ROMN	; LAST ROM DRIVE BANK

BID_RAMD0	.EQU	BID_RAM0	; FIRST RAM DRIVE BANK
BID_RAMDN	.EQU	BID_RAMN - 4	; LAST RAM DRIVE BANK
BID_AUX		.EQU	BID_RAMN - 3	; AUX BANK (BPBIOS, ETC.)
BID_BIOS	.EQU	BID_RAMN - 2	; BIOS BANK
BID_USR		.EQU	BID_RAMN - 1	; USER BANK (CP/M TPA, ETC.)
BID_COM		.EQU	BID_RAMN	; COMMON BANK, UPPER 32K
;
; MEMORY LAYOUT
;
SYS_SIZ		.EQU	$3000			; COMBINED SIZE OF SYSTEM AREA (OS + HBIOS PROXY)
HBBUF_SIZ	.EQU	1024			; INVARIANT HBIOS PHYSICAL DISK BUFFER, 1K
HBX_SIZ		.EQU	$200			; HBIOS PROXY SIZE (SUBJECT TO CHANGE)
CPM_SIZ		.EQU	SYS_SIZ - HBX_SIZ	; NET SIZE OF ALL OS COMPONENTS (EXCLUDING HBIOS PROXY)
CCP_SIZ		.EQU	$800			; INVARIANT SIZE OF CCP
BDOS_SIZ	.EQU	$E00			; INVARIANT SIZE OF BDOS
CBIOS_SIZ	.EQU	CPM_SIZ - CCP_SIZ - BDOS_SIZ	; CBIOS IS THE REMAINDER

MEMTOP		.EQU	$10000			; INVARIANT TOP OF Z80 ADDRESSABLE MEMORY
BNKTOP		.EQU	$8000			; BANK MEMORY BARRIER

HBX_IMG		.EQU	$200			; LOC OF HBX IMAGE IN HBIOS IMAGE BANK

HBBUF_END	.EQU	BNKTOP			; END OF PHYSICAL DISK BUFFER IN HBIOS
HBBUF_LOC	.EQU	HBBUF_END - HBBUF_SIZ	; START OF PHYSICAL DISK BUFFER
HBX_END		.EQU	MEMTOP			; END OF HBIOS PROXY
HBX_LOC		.EQU	HBX_END - HBX_SIZ	; START OF HBIOS PROXY
CPM_END		.EQU	HBX_LOC			; END OF CPM COMPONENTS (INCLUDING CBIOS)
CPM_LOC		.EQU	CPM_END - CPM_SIZ	; START OF CPM COMPONENTS
CBIOS_END	.EQU	HBX_LOC			; END OF CBIOS
CBIOS_LOC	.EQU	CBIOS_END - CBIOS_SIZ	; START OF CBIOS

CPM_ENT		.EQU	CBIOS_LOC		; CPM ENTRY POINT (IN CBIOS)

MON_LOC		.EQU	$C000			; LOCATION OF MONITOR FOR RUNNING SYSTEM
MON_SIZ		.EQU	$1000			; SIZE OF MONITOR BINARY IMAGE
MON_END		.EQU	MON_LOC + MON_SIZ	; END OF MONITOR

MON_DSKY	.EQU	MON_LOC + (0 * 3)	; MONITOR ENTRY (DSKY)
MON_SERIAL	.EQU	MON_LOC + (1 * 3)	; MONITOR ENTRY (SERIAL PORT)
;
; HELPER MACROS
;
#DEFINE	PRTC(C)	CALL PRTCH \ .DB C			; PRINT CHARACTER C TO CONSOLE - PRTC('X')
#DEFINE	PRTS(S)	CALL PRTSTRD \ .TEXT S			; PRINT STRING S TO CONSOLE - PRTD("HELLO")
#DEFINE	PRTX(X) CALL PRTSTRI \ .DW X			; PRINT STRING AT ADDRESS X TO CONSOLE - PRTI(STR_HELLO)
;
#DEFINE	XIO_PRTC(C)	CALL XIO_PRTCH \ .DB C		; PRINT CHARACTER C TO CONSOLE - PRTC('X')
#DEFINE	XIO_PRTS(S)	CALL XIO_PRTSTRD \ .DB S	; PRINT STRING S TO CONSOLE - PRTD("HELLO")
#DEFINE	XIO_PRTX(X)	CALL XIO_PRTSTRI \ .DW X	; PRINT STRING AT ADDRESS X TO CONSOLE - PRTI(STR_HELLO)
