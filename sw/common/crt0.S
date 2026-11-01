# Startup code: set up the stack, clear .bss, call main.
#
# pipeRV starts at address 0 after reset. There is no operating system and no
# C library, so this is everything that runs before main().

    .section .text.init
    .globl _start
_start:
    la    sp, __stack_top           # stack grows down from the end of the data memory

    la    t0, __bss_start           # zero-initialised globals
    la    t1, __bss_end
1:  bgeu  t0, t1, 2f
    sw    zero, 0(t0)
    addi  t0, t0, 4
    j     1b

2:  call  main
3:  j     3b                        # main returned: stop here