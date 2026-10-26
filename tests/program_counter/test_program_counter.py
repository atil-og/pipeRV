import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def setup(dut):
    """Start the clock, drive all inputs to a known state and apply reset."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.stall.value = 0
    dut.pc_sel.value = 0
    dut.pc_target.value = 0
    dut.rst_n.value = 0
    await step(dut, 2)
    dut.rst_n.value = 1


async def step(dut, cycles=1):
    """Wait for the given number of rising edges, then let outputs settle."""
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


def pc(dut):
    return dut.pc.value.to_unsigned()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_reset_value(dut):
    """PC is 0 after reset."""
    await setup(dut)
    assert pc(dut) == 0, f"PC after reset is 0x{pc(dut):08x}, expected 0"


@cocotb.test()
async def test_count(dut):
    """PC increments by 4 every clock cycle."""
    await setup(dut)
    for i in range(1, 9):
        await step(dut)
        assert pc(dut) == i * 4, f"cycle {i}: PC is 0x{pc(dut):08x}, expected 0x{i * 4:08x}"


@cocotb.test()
async def test_async_reset(dut):
    """Reset takes effect immediately, without waiting for a clock edge."""
    await setup(dut)
    await step(dut, 5)
    assert pc(dut) == 20

    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    assert pc(dut) == 0, f"PC is 0x{pc(dut):08x} right after reset, expected 0"

    dut.rst_n.value = 1
    await step(dut)
    assert pc(dut) == 4, f"PC is 0x{pc(dut):08x} after leaving reset, expected 0x4"


@cocotb.test()
async def test_stall(dut):
    """PC holds its value while stall is high and continues afterwards."""
    await setup(dut)
    await step(dut, 3)
    assert pc(dut) == 12

    dut.stall.value = 1
    await step(dut, 4)
    assert pc(dut) == 12, f"PC is 0x{pc(dut):08x} during stall, expected 0xc"

    dut.stall.value = 0
    await step(dut)
    assert pc(dut) == 16, f"PC is 0x{pc(dut):08x} after stall, expected 0x10"


@cocotb.test()
async def test_jump(dut):
    """PC loads the target when pc_sel is high and counts on from there."""
    await setup(dut)
    await step(dut, 2)

    dut.pc_target.value = 0x100
    dut.pc_sel.value = 1
    await step(dut)
    assert pc(dut) == 0x100, f"PC is 0x{pc(dut):08x} after jump, expected 0x100"

    dut.pc_sel.value = 0
    await step(dut, 2)
    assert pc(dut) == 0x108, f"PC is 0x{pc(dut):08x} two cycles after jump, expected 0x108"


@cocotb.test()
async def test_jump_overrides_stall(dut):
    """A jump wins over a stall."""
    await setup(dut)
    await step(dut, 2)

    dut.stall.value = 1
    dut.pc_target.value = 0x200