/* Memory layout of pipeRV (Harvard: separate instruction and data memory).
 *
 *   0x0000_0000  instruction memory, 4 KiB   code
 *   0x0001_0000  data memory, 4 KiB          .data, .rodata, .bss, stack
 *   0x8000_0000  memory-mapped I/O           see pipeRV.h
 *
 * Loads cannot read the instruction memory, so constants (.rodata) and
 * initialised variables (.data) go into the data memory. Its initial contents
 * are part of the FPGA bitstream. They are only restored by reprogramming the
 * FPGA, not by the reset button.
 */

OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY
{
  IMEM (rx) : ORIGIN = 0x00000000, LENGTH = 4K
  DMEM (rw) : ORIGIN = 0x00010000, LENGTH = 4K
}

SECTIONS
{
  .text : { *(.text.init) *(.text .text.*) } > IMEM

  .data : {
    *(.rodata .rodata.* .srodata .srodata.*)
    *(.data .data.* .sdata .sdata.*)
  } > DMEM

  .bss (NOLOAD) : {
    . = ALIGN(4);
    __bss_start = .;
    *(.bss .bss.* .sbss .sbss.* COMMON)
    . = ALIGN(4);
    __bss_end = .;
  } > DMEM

  __stack_top = ORIGIN(DMEM) + LENGTH(DMEM);
}
