import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from helpers.instruction_memory_model import InstructionMemoryModel



@cocotb.test()
async def test_instruction_fetch(dut):

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())


    dut.rst_n.value = 0

    imem_model = InstructionMemoryModel(memory = dut.imem_inst.memory)
    imem_model.load([
            0x00000013,  # NOP (addi x0, x0, 0)
            0x00100093,  # ADDI x1, x0, 1
            0x00200113,  # ADDI x2, x0, 2
            0x00300193   # ADDI x3, x0, 3
        ])

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    for cycle in range(4):
        await RisingEdge(dut.clk)
        await Timer(1, unit = "ns")

        cocotb.log.info(f"Clock cycle {cycle} -> instr_out: {hex(dut.instr_out.value)}")


    

