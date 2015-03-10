;clears the screen and waits some seconds
main
    stmfd sp!, {lr}
    mov r0, #0xC0000000
    ldr r0, [r0, #0x10]
    mvn r1, #0
    bl clrscrCX
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

clrscrCX ;base, color
    stmfd sp!, {r4-r7,lr}
    mov r4, r0;base
    mov r5, #0;x
    mov r6, #0;y
    mov r7, r1;color
xloop
    mov r0, r4
    mov r1, r5
    mov r2, r6
    mov r3, r7
    bl setPixelColorCX
    add r5, r5, #1;x++
    cmp r5, #320
    blt xloop
    mov r5, #0;x=0
    add r6, r6, #1;y++
    cmp r6, #240
    blt xloop
    ldmfd sp!, {r4-r7,pc}

setPixelColorCX ;base, x, y, color
    add r0, r0, r1, lsl #1
    add r0, r0, r2, lsl #9
    add r0, r0, r2, lsl #7
    strh r3, [r0]
    bx lr
