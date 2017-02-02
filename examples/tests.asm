;tests
main
    stmfd sp!, {lr}
    bl wait
    ldmfd sp!, {pc}
    
wait
    mvn r0, #0
    mov r0, r0, lsr #3
waitloop
    sub r0, r0, #1
    cmp r0, #0
    bgt waitloop
    bx lr

testvar dcw 0x12BC
    dcw 0112345

