# Makefile
export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# riscv_pkg must come first, the other modules import it
VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/alu.sv
VERILOG_SOURCES += $(PWD)/../../rtl/branch_unit.sv
VERILOG_SOURCES += $(PWD)/../../rtl/execute_stage.sv

TOPLEVEL = execute_stage
MODULE = test_execute_stage

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim