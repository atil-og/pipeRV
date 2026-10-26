import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from helpers.instruction_memory_model import InstructionMemoryModel


NOP = 0x00000013  # addi x0, x0, 0


def addi(rd, imm):
    """Encode addi rd, x0, imm. Used to fill memory with distinct instructions."""
    return ((imm & 0xFFF) << 20) | (rd << 7) | 0x13


# Every word is unique, so a wrong fetch address shows up immediately.
# Word i holds "addi x(i+1), x0, i+1", nothing in here equals NOP.
PROGRAM = [addi((i % 31) + 1, i + 1) for i in range(16)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def setup(dut):
    """Start the clock, load the program, drive inputs and apply reset."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.stall.value = 0
    dut.pc_sel.value = 0
    dut.pc_target.value = 0
    dut.rst_n.value = 0

    InstructionMemoryModel(dut.imem_inst.memory).load(PROGRAM)

    await step(dut, 2)
    dut.rst_n.value = 1


async def step(dut, cycles=1):
    """Wait for the given number of rising edges, then let outputs settle."""
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


def check(dut, instr, pc, label=""):
    got_instr = dut.instr_out.value.to_unsigned()
    got_pc = dut.pc_out.value.to_unsigned()
    assert got_instr == instr, f"{label}: instr_out=0x{got_instr:08x}, expected 0x{instr:08x}"
    assert got_pc == pc, f"{label}: pc_out=0x{got_pc:08x}, expected 0x{pc:08x}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_reset(dut):
    """During reset the output is a NOP at PC 0."""
    await setup(dut)
    check(dut, NOP, 0, "reset")


@cocotb.test()
async def test_sequential_fetch(dut):
    """Instructions come out in order, each with its own PC."""
    await setup(dut)
    for i in range(len(PROGRAM)):
        await step(dut)
        check(dut, PROGRAM[i], i * 4, f"cycle {i}")


@cocotb.test()
async def test_stall(dut):
    """Output holds during a stall and continues with the next instruction afterwards."""
    await setup(dut)
    await step(dut, 3)
    check(dut, PROGRAM[2], 8, "before stall")

    dut.stall.value = 1
    for i in range(3):
        await step(dut)
        check(dut, PROGRAM[2], 8, f"stall cycle {i}")

    dut.stall.value = 0
    await step(dut)
    check(dut, PROGRAM[3], 12, "after stall")


@cocotb.test()
async def test_jump_flush(dut):
    """A jump flushes the fetched instruction and continues at the target."""
    await setup(dut)
    await step(dut, 2)
    check(dut, PROGRAM[1], 4, "before jump")

    dut.pc_target.value = 0x20  # word 8
    dut.pc_sel.value = 1
    await step(dut)
    assert dut.instr_out.value.to_unsigned() == NOP, "instruction was not flushed"

    dut.pc_sel.value = 0
    await step(dut)
    check(dut, PROGRAM[8], 0x20, "jump target")

    await step(dut)
    check(dut, PROGRAM[9], 0x24, "after jump target")