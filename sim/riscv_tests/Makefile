# Runs the official riscv-tests (rv32ui) on pipeRV.
#
#   make                   build all test programs, then simulate them
#   make TESTS="add lw"    only these tests
#   make programs          only build the programs
#   make clean
#
# Needs the RISC-V GCC (Ubuntu/Debian: apt install gcc-riscv64-unknown-elf)
# and the riscv-tests sources in third_party/riscv-tests (git submodule).

export COCOTB_LOG_LEVEL = INFO
export PYTHONPATH := $(PWD):$(PWD)/..:$(PYTHONPATH)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# riscv_pkg must come first, the other modules import it
VERILOG_SOURCES += $(PWD)/../../rtl/riscv_pkg.sv
VERILOG_SOURCES += $(filter-out %/riscv_pkg.sv,$(wildcard $(PWD)/../../rtl/*.sv))

TOPLEVEL = cpu_top
MODULE = test_riscv_tests

# ---------------------------------------------------------------------------
# Test programs
# ---------------------------------------------------------------------------

RISCV_TESTS ?= $(PWD)/../../third_party/riscv-tests
RISCV_PREFIX ?= riscv64-unknown-elf-
BUILD := $(PWD)/build

# All rv32ui tests except two that pipeRV cannot pass by design:
#   fence_i  self-modifying code; instruction and data memory are separate
#   ma_data  misaligned loads/stores; flagged in MEM but not performed correctly
# They can still be run explicitly: make TESTS="fence_i ma_data"
TESTS ?= simple add addi and andi auipc beq bge bgeu blt bltu bne \
         jal jalr lb lbu lh lhu lw ld_st lui or ori sb sh sw st_ld \
         sll slli slt slti sltiu sltu sra srai srl srli sub xor xori

export TESTS
export BUILD

CFLAGS := -march=rv32i_zifencei -mabi=ilp32 -static -nostdlib -nostartfiles -Wl,--no-relax \
          -I $(PWD)/env -I $(RISCV_TESTS)/isa/macros/scalar -T $(PWD)/env/link.ld

PROGRAMS := $(foreach t,$(TESTS),$(BUILD)/$(t).text.bin $(BUILD)/$(t).data.bin)

# Keep the .elf files, they are needed for debugging
.SECONDARY:

.PHONY: programs
programs: $(PROGRAMS)

$(BUILD)/%.elf: $(RISCV_TESTS)/isa/rv32ui/%.S $(PWD)/env/riscv_test.h $(PWD)/env/link.ld
	@mkdir -p $(BUILD)
	$(RISCV_PREFIX)gcc $(CFLAGS) $< -o $@
	$(RISCV_PREFIX)objdump -d $@ > $(BUILD)/$*.dump

$(BUILD)/%.text.bin: $(BUILD)/%.elf
	$(RISCV_PREFIX)objcopy -O binary -j .text $< $@

$(BUILD)/%.data.bin: $(BUILD)/%.elf
	$(RISCV_PREFIX)objcopy -O binary -j .data $< $@

include $(shell cocotb-config --makefiles)/Makefile.sim

# 'programs' is defined first, so make the simulation the default target
.DEFAULT_GOAL := sim

# Build the programs before simulating
$(COCOTB_RESULTS_FILE): $(PROGRAMS)

clean::
	rm -rf $(BUILD)