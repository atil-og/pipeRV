# Runs C programs from sw/ on cpu_top. The program is built with a short delay
# and loaded through the IMEM_INIT / DMEM_INIT parameters, like on the FPGA.

export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# riscv_pkg must come first, the other modules import it
VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(filter-out %/riscv_pkg.sv,$(wildcard $(PWD)/../../rtl/*.sv))

TOPLEVEL = cpu_top
MODULE = test_programs

SW    := $(abspath $(PWD)/../../sw)
BUILD := $(PWD)/build
PROG  := blink

COMPILE_ARGS += -Pcpu_top.IMEM_INIT=\"$(BUILD)/$(PROG).imem.hex\"
COMPILE_ARGS += -Pcpu_top.DMEM_INIT=\"$(BUILD)/$(PROG).dmem.hex\"

include $(shell cocotb-config --makefiles)/Makefile.sim

.DEFAULT_GOAL := sim

# Build the program with a short delay, so the simulation does not take forever
.PHONY: program
program:
	$(MAKE) -C $(SW) PROG=$(PROG) BUILD=$(BUILD) CFLAGS_EXTRA=-DDELAY=5

$(SIM_BUILD)/sim.vvp: program

clean::
	rm -rf $(BUILD)