"""Run C programs from sw/ on cpu_top, exactly as the FPGA would.

The Makefile builds sw/blink with a short delay and loads the same .hex files
the FPGA bitstream uses, through the IMEM_INIT / DMEM_INIT parameters.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Edge, FallingEdge, RisingEdge, Timer, with_timeout


async def start(dut, switches=0):
    dut.switches.value = switches
    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1


async def next_leds(dut):
    """Wait for the next change of the LED register and return the new value."""
    await with_timeout(Edge(dut.leds), 100, "us")
    await FallingEdge(dut.clk)
    return int(dut.leds.value)


@cocotb.test()
async def test_blink_running_light(dut):
    """The light runs from LD0 to LD7 and back."""
    await start(dut)

    seen = [await next_leds(dut) for _ in range(16)]
    expected = [1 << i for i in range(8)] + [1 << i for i in range(6, -1, -1)] + [2]
    assert seen == expected, f"LED sequence {[hex(v) for v in seen]}, expected {[hex(v) for v in expected]}"


@cocotb.test()
async def test_blink_mirror_switches(dut):
    """With SW7 up the LEDs show the switches, and follow them when they change."""
    await start(dut, switches=0x80 | 0x35)
    assert await next_leds(dut) == 0xB5, "LEDs do not mirror the switches"

    dut.switches.value = 0x80 | 0x0F
    value = await next_leds(dut)
    assert value == 0x8F, f"LEDs = {value:#x} after changing the switches, expected 0x8f"