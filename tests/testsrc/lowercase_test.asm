 cmp R1, #0x1000
 cmp R1, #0x1
 cmp R1, #0x10
 sub R2, R0, #1
 rsb R2, R1, R2
 cmp R3, #0
 andeqs R0, R1, R2
 andeq R0, R1, R2
 bls nullsub
 swi #5
 strb R1, [R2, R4]!
 str R1, [R2], R4
 str R1, [R2, R4, LSL #2]
 ldr R13, [PC, #20]
 str R1, [R3, #-100]!
 str R1, sramaddr
 swp R0, R4, [SP]
 swpb R0, R4, [SP]
 ldrsh R10, [SP, #4]
 mul SP, R4, R0
 umlals R1,R5,R2,R3
 msr CPSR_all, R5
 msr CPSR_flg,#0xA0000000
 mrs R1, SPSR
 ldmfd SP!,{R0,R1,R2}
 stmfd R13,{R0-R14}^
 mcr p15,0, R0, c8, c5, 0
lolsub
 b lolsub
sramaddr dcd 0xA4000000
teststr dcb "hello world!",0
 align
nullsub bx LR