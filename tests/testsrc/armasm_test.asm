 CMP R1, #0x1000
 CMP R1, #0x1
 CMP R1, #0x10
 CMP R1, #0xE0
 CMP R1, #0x100
 CMP R1, #0x10000
 CMP R1, #0x100000
 SUB R2, R0, #1
 RSB R2, R1, R2
 CMP R3, #0
 ANDEQS R0, R1, R2
 ANDEQ R0, R1, R2
 BLS nullsub
 SWI #5
 STRB R1, [R2, R4]!
 STR R1, [R2], R4
 STR R1, [R2, R4, LSL #2]
 LDR R13, [PC, #20]
 STR R1, [R3, #-100]!
 STR R1, sramaddr
 SWP R0, R4, [SP]
 SWPB R0, R4, [SP]
 LDRSH R10, [SP, #4]
 MUL SP, R4, R0
 UMLALS R1,R5,R2,R3
 MSR CPSR_all, R5
 MSR CPSR_flg,#0xA0000000
 MRS R1, SPSR
 LDMFD SP!,{R0,R1,R2}
 STMFD R13,{R0-R14}^
 MCR p15,0, R0, c8, c5, 0
lolsub
 B lolsub
sramaddr DCD 0xA4000000
teststr DCB "hello world!",0
 ALIGN
nullsub BX LR