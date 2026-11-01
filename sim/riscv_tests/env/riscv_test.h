// Test environment for running the official riscv-tests on pipeRV.
//
// The standard environments (env/p, env/v) use CSRs, ecall and a tohost
// section, which pipeRV does not support yet. This one only needs RV32I:
//
//   - every test starts at address 0 and clears all registers
//   - the result is reported by storing it to the address TOHOST:
//       1                    -> all test cases passed
//       (case number << 1)|1 -> that test case failed
//   - afterwards the program loops on itself
//
// The testbench watches for the store to TOHOST.

#ifndef _ENV_PIPERV_H
#define _ENV_PIPERV_H

#define TOHOST 0x00020000

#define RVTEST_RV32U .macro init; .endm
#define RVTEST_RV64U .macro init; .endm

#define TESTNUM gp

#define INIT_XREG                                                       \
  li x1, 0;  li x2, 0;  li x3, 0;  li x4, 0;  li x5, 0;  li x6, 0;      \
  li x7, 0;  li x8, 0;  li x9, 0;  li x10, 0; li x11, 0; li x12, 0;     \
  li x13, 0; li x14, 0; li x15, 0; li x16, 0; li x17, 0; li x18, 0;     \
  li x19, 0; li x20, 0; li x21, 0; li x22, 0; li x23, 0; li x24, 0;     \
  li x25, 0; li x26, 0; li x27, 0; li x28, 0; li x29, 0; li x30, 0;     \
  li x31, 0;

#define RVTEST_CODE_BEGIN                                               \
        .section .text.init;                                            \
        .globl _start;                                                  \
_start:                                                                 \
        INIT_XREG;                                                      \
        init;

#define RVTEST_CODE_END                                                 \
1:      j 1b;

#define RVTEST_PASS                                                     \
        fence;                                                          \
        li TESTNUM, 1;                                                  \
        li t5, TOHOST;                                                  \
        sw TESTNUM, 0(t5);                                              \
1:      j 1b;

#define RVTEST_FAIL                                                     \
        fence;                                                          \
1:      beqz TESTNUM, 1b;                                               \
        sll TESTNUM, TESTNUM, 1;                                        \
        or TESTNUM, TESTNUM, 1;                                         \
        li t5, TOHOST;                                                  \
        sw TESTNUM, 0(t5);                                              \
2:      j 2b;

#define EXTRA_DATA

#define RVTEST_DATA_BEGIN                                               \
        EXTRA_DATA                                                      \
        .align 4; .global begin_signature; begin_signature:

#define RVTEST_DATA_END .align 4; .global end_signature; end_signature:

#endif