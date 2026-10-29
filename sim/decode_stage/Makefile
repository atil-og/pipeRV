# Makefile
export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# riscv_pkg must come first, the other modules import it
VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/immediate_generator.sv
VERILOG_SOURCES += $(PWD)/../../rtl/instruction_decoder.sv
VERILOG_SOURCES += $(PWD)/../../rtl/control_unit.sv
VERILOG_SOURCES += $(PWD)/../../rtl/register_file.sv
VERILOG_SOURCES += $(PWD)/../../rtl/decode_stage.sv

TOPLEVEL = decode_stage
MODULE = test_decode_stage

WAVES = 1

# Cocotb-Makefiles einbinden
include $(shell cocotb-config --makefiles)/Makefile.sim