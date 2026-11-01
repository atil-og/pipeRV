/* pipeRV has separate instruction and data memories (Harvard).
 * Code goes to the instruction memory starting at 0, data to the data memory.
 * The data memory only decodes the low address bits, so DATA_BASE maps to
 * word 0 of the data memory. */

OUTPUT_ARCH("riscv")
ENTRY(_start)

DATA_BASE = 0x00010000;

SECTIONS
{
  . = 0x00000000;
  .text : { *(.text.init) *(.text .text.*) }

  . = DATA_BASE;
  .data : { *(.data .data.*) *(.sdata .sdata.*) *(.rodata .rodata.*) }
  .bss  : { *(.bss .bss.*) *(.sbss .sbss.*) }

  _end = .;
}
