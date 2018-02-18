nAssembler
==========

Assembler for TI Nspire ARM, running on-calc or on computer
Written in python. You need micropython on your calc to use it.

Usage
-----
Install micropython on your calc.
Launch the nassembler.py.tns file using micropython.
The program will ask you to specify the input file (containing the assembly source code)
and the output file (where the binary will be stored).
You have to specify the full path (for example /documents/test/clrscr.asm.tns)
If there are no errors, micropython will now tell you "Press any key to exit".
You should now see the output file after refreshing the docbrowser
(just go to the homescreen and back to the docbrowser).

Assembly language
-----------------
(Also look at the examples)
IMPORTANT (syntax is not very flexible at the moment):
-Instruction names must be preceded by whitespace
-Labels must not be preceded by any whitespace
-The instruction names and syntax are like in standard ARM assembly
(like in the official ARM online documentation)
-No automatic substitution of e.g. MVN for MOV if the immediate value can only be encoded in the inverted case
-Two operands were three are required is not allowed (no implicit destination register), e.g. "ADD r0,#28" must be written out as "ADD r0,r0,#28"

All usual instructions are supported:
ADC(S), ADD(S), AND(S), B, BIC(S), BL, BX, CLZ, CMP, CMN,
EOR(S), LDM.., LDR(B/T/BT/H/SH/SB), MCR, MLA(S), MOV(S),
MRC, MRS, MSR, MUL(S), MVN(S), ORR(S),
RSB(S), RSC(S), SBC(S), SMLAL(S), SMULL(S), STM..,
STR(B/T/BT/H), SUB(S), SVC/SWI, SWP(B), TEQ, TST, UMLAL(S), UMULL(S)

The ALIGN, DCD, DCDU, DCW, DCWU, DCB, INCBIN and INCLUDE directives are supported.

The ADR pseudo instruction is now also implemented.

Some other pseudo instruction (like PUSH etc) are not implemented.
Other instructions may be missing (report if you need one).

The first line of the source is also the entry point of the program.

Numeric literals:
Prefix with 0x for hexadecimal numbers, 0 for octal, 0b for binary.
Single characters enclosed in single quotes ' are interpreted as their ascii value
You can use DCB "some string" to create a string.

Feature suggestions/Bug reports
-------------------------------
Topic on tiplanet: https://tiplanet.org/forum/viewtopic.php?t=16174&p=178789
You can also email me (lkjcalc@gmail.com)

