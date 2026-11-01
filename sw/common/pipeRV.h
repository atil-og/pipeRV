// Memory-mapped I/O of pipeRV, see rtl/mmio.sv
#ifndef PIPERV_H
#define PIPERV_H

#include <stdint.h>

#define LEDS     (*(volatile uint32_t *)0x80000000u)   // write: bits [7:0] drive LD0..LD7
#define SWITCHES (*(volatile uint32_t *)0x80000004u)   // read:  bits [7:0] are SW0..SW7

#endif