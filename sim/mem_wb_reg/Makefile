export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog


VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/mem_wb_reg.sv
TOPLEVEL = mem_wb_reg
MODULE = test_mem_wb_reg

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim