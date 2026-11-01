# Build a C program for pipeRV.
#
#   make                     builds sw/blink
#   make PROG=foo            builds sw/foo (all .c and .S files in that folder)
#   make PROG=blink CFLAGS_EXTRA=-DDELAY=10    e.g. a short delay for simulation
#
# Output in build/:
#   <prog>.elf        executable
#   <prog>.dump       disassembly
#   <prog>.imem.hex   instruction memory image ($readmemh)
#   <prog>.dmem.hex   data memory image ($readmemh)

PROG ?= blink
PREFIX ?= riscv64-unknown-elf-
BUILD := build

CFLAGS := -march=rv32i -mabi=ilp32 -O2 -ffreestanding -nostdlib -nostartfiles \
          -ffunction-sections -fdata-sections -Wall -Wextra \
          -I common $(CFLAGS_EXTRA)
LDFLAGS := -T common/link.ld -Wl,--gc-sections -Wl,--no-relax

SOURCES := common/crt0.S $(wildcard $(PROG)/*.c $(PROG)/*.S)

.PHONY: all clean
all: $(BUILD)/$(PROG).imem.hex $(BUILD)/$(PROG).dmem.hex $(BUILD)/$(PROG).dump

$(BUILD)/$(PROG).elf: $(SOURCES) common/link.ld common/pipeRV.h
	@mkdir -p $(BUILD)
	$(PREFIX)gcc $(CFLAGS) $(LDFLAGS) $(SOURCES) -lgcc -o $@
	$(PREFIX)size $@

$(BUILD)/%.dump: $(BUILD)/%.elf
	$(PREFIX)objdump -d $< > $@

$(BUILD)/%.imem.bin: $(BUILD)/%.elf
	$(PREFIX)objcopy -O binary -j .text $< $@

$(BUILD)/%.dmem.bin: $(BUILD)/%.elf
	$(PREFIX)objcopy -O binary -j .data $< $@

$(BUILD)/%.hex: $(BUILD)/%.bin
	python3 tools/bin2hex.py $< $@

clean:
	rm -rf $(BUILD)