# Build and load pipeRV on the ZedBoard.
#
#   make                 build sw/blink and the bitstream
#   make PROG=foo        another program from sw/
#   make program         load the bitstream over JTAG
#
# Needs the RISC-V GCC and Vivado (vivado in PATH).

PROG ?= blink
SW   := ../sw
BUILD := build

WIN_DIR ?= /mnt/c/pipeRV_fpga


.PHONY: all bitstream program clean
all: bitstream

$(BUILD)/imem.mem $(BUILD)/dmem.mem: FORCE
	$(MAKE) -C $(SW) PROG=$(PROG)
	@mkdir -p $(BUILD)
	cp $(SW)/build/$(PROG).imem.hex $(BUILD)/imem.mem
	cp $(SW)/build/$(PROG).dmem.hex $(BUILD)/dmem.mem

bitstream: $(BUILD)/imem.mem $(BUILD)/dmem.mem
	vivado -mode batch -nojournal -log $(BUILD)/vivado.log -source build.tcl

program:
	vivado -mode batch -nojournal -log $(BUILD)/program.log -source program.tcl

clean:
	rm -rf $(BUILD) .Xil

FORCE:


.PHONY: export-windows
export-windows: $(BUILD)/imem.mem $(BUILD)/dmem.mem
	rm -rf $(WIN_DIR)
	mkdir -p $(WIN_DIR)/fpga/build
	cp -r ../rtl $(WIN_DIR)/
	cp zedboard_top.sv zedboard.xdc build.tcl program.tcl $(WIN_DIR)/fpga/
	cp $(BUILD)/imem.mem $(BUILD)/dmem.mem $(WIN_DIR)/fpga/build/
	@echo "Windows: cd C:/pipeRV_fpga/fpga, then source build.tcl"