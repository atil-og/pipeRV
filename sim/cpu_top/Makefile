# Makefile
export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# riscv_pkg must come first, the other modules import it
VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(filter-out %/riscv_pkg.sv,$(wildcard $(PWD)/../../rtl/*.sv))

TOPLEVEL = cpu_top
MODULE = test_cpu_top

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim