import random

import cocotb
from cocotb.triggers import Timer


# Must match riscv_pkg.sv
WB_ALU, WB_MEM, WB_PC4 = 0, 1, 2


def wb_ctrl(reg_write=0, wb_sel=0):
    """Pack wb_ctrl_t: {reg_write, wb_sel[1:0]}."""
    return (reg_write << 2) | wb_sel


async def apply(dut, reg_write, wb_sel, alu_result, load_data, pc_plus4, rd):
    dut.wb_ctrl.value = wb_ctrl(reg_write, wb_sel)
    dut.alu_result.value = alu_result
    dut.load_data.value = load_data
    dut.pc_plus4.value = pc_plus4
    dut.rd.value = rd
    await Timer(1, unit="ns")


@cocotb.test()
async def test_select(dut):
    """wb_sel picks ALU result, load data or pc + 4."""
    alu, mem, pc4 = 0x11111111, 0x22222222, 0x33333333
    for wb_sel, expected, name in ((WB_ALU, alu, "ALU"), (WB_MEM, mem, "MEM"), (WB_PC4, pc4, "PC+4")):
        await apply(dut, 1, wb_sel, alu, mem, pc4, rd=5)
        got = int(dut.wb_data.value)
        assert got == expected, f"wb_sel={name}: wb_data = 0x{got:08x}, expected 0x{expected:08x}"


@cocotb.test()
async def test_unused_select(dut):
    """wb_sel = 3 is not used and must give 0 instead of an X."""
    await apply(dut, 1, 0b11, 0x1, 0x2, 0x3, rd=5)
    assert int(dut.wb_data.value) == 0, "wb_sel = 3 does not give 0"


@cocotb.test()
async def test_pass_through(dut):
    """reg_write and rd are passed straight to the register file port."""
    for _ in range(100):
        reg_write = random.randint(0, 1)
        rd = random.getrandbits(5)
        await apply(dut, reg_write, random.choice((WB_ALU, WB_MEM, WB_PC4)),
                    random.getrandbits(32), random.getrandbits(32), random.getrandbits(32), rd)
        assert int(dut.reg_write.value) == reg_write, "reg_write not passed through"
        assert int(dut.wb_rd.value) == rd, f"wb_rd = {int(dut.wb_rd.value)}, expected {rd}"