# Makefile
export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog



# sim/memory_stage/Makefile
VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/data_memory.sv
VERILOG_SOURCES += $(PWD)/../../rtl/memory_stage.sv
TOPLEVEL = memory_stage
MODULE = test_memory_stage


WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim