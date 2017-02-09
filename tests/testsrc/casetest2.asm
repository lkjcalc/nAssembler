 str r1, [r2]
 umlals r1, r6, r3, r5
 msr cpsr_all, r5
 mrc P15, 0, r0, C8, C5, 0
 bx lr
 cmp r1, #1
 add r1, r2, r3
 mov r2, r3
 andeqs r0, r1, r2
 swi #10
 str r1, [r3, r4]!
 ldrsh r1, [r3, r4]
 swp r0, r4, [sp]
 mul r1, r2, r3
 ldmfd sp!,{r0-r4}
