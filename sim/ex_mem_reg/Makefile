# Makefile
export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog


VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/ex_mem_reg.sv
TOPLEVEL = ex_mem_reg
MODULE = test_ex_mem_reg


WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim