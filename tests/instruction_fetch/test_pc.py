import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import logging

@cocotb.test()
async def test_pc_basic(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    await test_pc_count(dut)
    await test_value_of_pc_at_reset(dut)

async def test_value_of_pc_at_reset(dut):

    logger = logging.getLogger("pc_testbench")

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    if dut.pc.value == 0:
        logger.info(f"test_value_of_pc_at_reset TEST PASSED | value of program counter after reset: {dut.pc.value}")
    else:
        logger.critical(f"test_value_of_pc_at_reset TEST FAILED | value of program counter after reset: {dut.pc.value}")


async def test_pc_count(dut):

    logger = logging.getLogger("pc_testbench")

    dut.rst_n.value = 1

    for i in range(1, 5):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if dut.pc.value == i * 4:
            logger.info(f"test_pc_count TEST PASSED | value of program counter: {dut.pc.value} after {i} clock cycle(s)")
        else:
            logger.critical(f"test_pc_count TEST FAILED | value of program counter: {dut.pc.value} after {i} clock cycle(s)")






    
    

        
