 CMP R1, #0x1000
 CMP R1,#0x1000
 SUB R2, R0, #1
 SUB R2,R0,#1
 ANDEQS R0, R1, R2
 ANDEQS R0,R1,R2
 STRB R1, [R2, R4]!
 STRB R1,[R2,R4]!
 STR R1,[R2],R4
 STR R1, [R2], R4
 STR R1, [R2, R4, LSL #2]
 STR R1,[R2,R4,LSL #2]
 LDR R13, [PC, #20]
 LDR R13,[PC,#20]
 STR R1, [R3, #-100]!
 STR R1,[R3,#-100]!
 STR R1, sramaddr
 STR R1,sramaddr2
 SWP R0, R4, [SP]
 SWP R0,R4,[SP]
 MUL SP, R4, R0
 MUL SP,R4,R0
 UMLALS R1,R5,R2,R3
 UMLALS R1 , R5 , R2 , R3
 MSR CPSR_all, R5
 MSR CPSR_all,R5
 MSR CPSR_flg,#0xA0000000
 MSR CPSR_flg, #0xA0000000
 MRS R1, SPSR
 MRS R1,SPSR
 LDMFD SP!,{R0,R1,R2}
 LDMFD SP! ,{R0, R1, R2}
 STMFD R13,{R0-R14}^
 STMFD R13 , {R0 - R14}^
 MCR p15,0,R0,c8,c5,0
 MCR p15 , 0 , R0 , c8 , c5 , 0
sramaddr DCD 0xA4000000
sramaddr2 DCDU 0xA4000000
