import random
import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
import random

async def setup(dut):
    """Start clock and bring every input into a stable state"""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.w_en.value = 0
    dut.write_destination.value = 0
    dut.write_data.value = 0
    dut.addr_reg_1.value = 0
    dut.addr_reg_2.value = 0
    await FallingEdge(dut.clk)

async def write_register(dut, addr, value, w_en = 1):
    dut.write_destination.value = addr
    dut.write_data.value = value
    dut.w_en.value = w_en
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.w_en.value = 0

async def read_regs(dut, addr1, addr2):
    dut.addr_reg_1.value = addr1
    dut.addr_reg_2.value = addr2
    await Timer(1, unit="ns")
    return dut.data_reg1.value.to_unsigned(), dut.data_reg2.value.to_unsigned()


@cocotb.test()
async def test_x0_is_zero(dut):
    """x0 must always be zero, write attempts have to be rejected"""
    await setup(dut)
 
    await write_register(dut, 0, 0xDEADBEEF)
    d1, d2 = await read_regs(dut, 0, 0)
 
    assert d1 == 0, f"x0 on port 1 0x{d1:08x}, expected 0"
    assert d2 == 0, f"x0 on port 2 0x{d2:08x}, expected 0"


@cocotb.test()
async def test_write_read_all_registers(dut):
    await setup(dut)


    expected = {addr : random.getrandbits(32) for addr in range(1, 32)}

    for addr, data in expected.items():
        await write_register(dut=dut, addr = addr, value = data)

    for addr, data in expected.items():
        d1, d2 = await read_regs(dut=dut, addr1=addr, addr2=addr)
        assert d1 == data, f"x{addr} Port 1: 0x{d1:08x}, expected 0x{data:08x}"
        assert d2 == data, f"x{addr} Port 2: 0x{d2:08x}, expected 0x{data:08x}"

