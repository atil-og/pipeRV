# Makefile
export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/../../rtl/program_counter.sv
VERILOG_SOURCES += $(PWD)/../../rtl/imem.sv
VERILOG_SOURCES += $(PWD)/../../rtl/instruction_fetch.sv

TOPLEVEL = instruction_fetch
MODULE = test_instruction_fetch

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim