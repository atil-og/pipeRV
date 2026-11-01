export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog


VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/writeback_stage.sv
TOPLEVEL = writeback_stage
MODULE = test_writeback_stage

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim