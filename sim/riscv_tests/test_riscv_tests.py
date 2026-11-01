"""Run the official riscv-tests (rv32ui) on cpu_top.

Each test program reports its result by storing to TOHOST (see env/riscv_test.h):
1 means all test cases passed, (n << 1) | 1 means test case n failed. The
testbench watches the EX/MEM register for that store.

The programs are built by the Makefile into $BUILD/<name>.text.bin and
$BUILD/<name>.data.bin. The list of tests comes from the TESTS variable.
"""

import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


TOHOST = 0x00020000
DATA_BASE = 0x00010000       # must match env/link.ld
TIMEOUT_CYCLES = 20000

BUILD = Path(os.environ.get("BUILD", "build"))
TESTS = os.environ.get("TESTS", "").split()


def words(path):
    """Read a binary file as little-endian 32-bit words."""
    data = path.read_bytes()
    data += b"\0" * (-len(data) % 4)
    return [int.from_bytes(data[i:i + 4], "little") for i in range(0, len(data), 4)]


def load(dut, name):
    imem = dut.fetch_inst.imem_inst.memory
    dmem = dut.memory_inst.dmem_inst.memory
    regs = dut.decode_inst.rf_inst.reg_file

    text = words(BUILD / f"{name}.text.bin")
    data = words(BUILD / f"{name}.data.bin")
    assert len(text) <= len(imem), f"{name}: {4 * len(text)} bytes of code do not fit into imem"

    # Build complete images and write every location exactly once.
    # Unused locations get 0: uninitialised memory is X in simulation and would
    # propagate through the pipeline when fetched or loaded.
    # Writing a location twice (first 0, then the data) does not work: cocotb
    # applies writes at the end of the time step, and which of two writes to the
    # same location wins is not defined.
    imem_image = text + [0] * (len(imem) - len(text))
    dmem_image = [0] * len(dmem)
    for i, word in enumerate(data):
        dmem_image[(DATA_BASE // 4 + i) % len(dmem)] = word

    for i, word in enumerate(imem_image):
        imem[i].value = word
    for i, word in enumerate(dmem_image):
        dmem[i].value = word
    for i in range(1, 32):
        regs[i].value = 0


async def run_until_tohost(dut):
    """Return the value stored to TOHOST, or None on timeout."""
    for _ in range(TIMEOUT_CYCLES):
        await FallingEdge(dut.clk)
        mem_write = int(dut.ex_mem_mem_ctrl.value) & 1          # mem_ctrl_t = {mem_read, mem_write}
        if mem_write and int(dut.ex_mem_alu_result.value) == TOHOST:
            return int(dut.ex_mem_store_data.value)
    return None


@cocotb.test()
@cocotb.parametrize(name=TESTS)
async def rv32ui(dut, name):
    # All tests run in the same simulation. The previous test stopped as soon as
    # it saw its TOHOST store in EX/MEM, before the memory wrote it. Reset first,
    # so that store is cleared out of the pipeline before the new clock's first
    # edge, otherwise it would overwrite the freshly loaded data.
    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    load(dut, name)

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    result = await run_until_tohost(dut)

    dump = BUILD / f"{name}.dump"
    assert result is not None, f"{name}: no result after {TIMEOUT_CYCLES} cycles (see {dump})"
    assert result == 1, (
        f"{name}: test case {result >> 1} failed. Search for 'test_{result >> 1}' in {dump}"
    )