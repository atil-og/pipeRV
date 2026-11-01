import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# Every input with its width; outputs have the same name with _out instead of _in
FIELDS = {
    "wb_ctrl":    3,
    "alu_result": 32,
    "load_data":  32,
    "pc_plus4":   32,
    "rd":         5,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def setup(dut):
    """Start the clock, drive all inputs to 0 and apply reset."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    drive(dut, {name: 0 for name in FIELDS})
    dut.rst_n.value = 0
    await step(dut, 2)
    dut.rst_n.value = 1


async def step(dut, cycles=1):
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


def drive(dut, values):
    for name, value in values.items():
        getattr(dut, f"{name}_in").value = value


def random_values():
    return {name: random.getrandbits(width) for name, width in FIELDS.items()}


def check(dut, expected, label):
    for name, value in expected.items():
        got = int(getattr(dut, f"{name}_out").value)
        assert got == value, f"{label}: {name}_out = 0x{got:x}, expected 0x{value:x}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_reset(dut):
    """All outputs are 0 after reset, so no register is written."""
    await setup(dut)
    check(dut, {name: 0 for name in FIELDS}, "after reset")


@cocotb.test()
async def test_pass_through(dut):
    """Every field arrives at the output one cycle later."""
    await setup(dut)
    for i in range(50):
        values = random_values()
        drive(dut, values)
        await step(dut)
        check(dut, values, f"cycle {i}")


@cocotb.test()
async def test_async_reset(dut):
    """Reset clears the outputs immediately, without a clock edge."""
    await setup(dut)
    drive(dut, random_values())
    await step(dut)

    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    check(dut, {name: 0 for name in FIELDS}, "right after reset")