# Makefile


SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/../rtl/program_counter.sv
VERILOG_SOURCES += $(PWD)/../rtl/imem.sv

TOPLEVEL ?= program_counter
MODULE ?= test_pc

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim