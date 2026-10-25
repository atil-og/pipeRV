import cocotb
import logging
from cocotb.triggers import Timer
from helpers.instruction_memory_model import InstructionMemoryModel

@cocotb.test()
async def test_imem(dut):
    logger = logging.getLogger("imem_testbench")

    imem_model = InstructionMemoryModel(dut = dut)
    imem_model.load([
        0x00000013,  # NOP
        0x00100093
    ])

    test_addresses = [0, 4]

    for address in test_addresses:
        dut.read_address.value = address
        await Timer(1, unit = "ns")

        logger.critical(f"{hex(dut.instr.value)}")
    
