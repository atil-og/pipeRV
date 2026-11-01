import random

import cocotb
from cocotb.triggers import Timer


FWD_NONE, FWD_WB, FWD_MEM = 0b00, 0b01, 0b10


def model(rs, ex_mem_reg_write, ex_mem_rd, mem_wb_reg_write, mem_wb_rd):
    """Reference: newest producer wins, x0 is never forwarded."""
    if ex_mem_reg_write and ex_mem_rd != 0 and ex_mem_rd == rs:
        return FWD_MEM
    if mem_wb_reg_write and mem_wb_rd != 0 and mem_wb_rd == rs:
        return FWD_WB
    return FWD_NONE


async def apply(dut, rs1, rs2, ex_mem_reg_write, ex_mem_rd, mem_wb_reg_write, mem_wb_rd):
    dut.id_ex_rs1.value = rs1
    dut.id_ex_rs2.value = rs2
    dut.ex_mem_reg_write.value = ex_mem_reg_write
    dut.ex_mem_rd.value = ex_mem_rd
    dut.mem_wb_reg_write.value = mem_wb_reg_write
    dut.mem_wb_rd.value = mem_wb_rd
    await Timer(1, unit="ns")
    return int(dut.forward_a.value), int(dut.forward_b.value)


@cocotb.test()
async def test_directed(dut):
    """The cases that matter, one by one."""
    cases = [
        # (rs1, rs2, ex_mem_wr, ex_mem_rd, mem_wb_wr, mem_wb_rd, fwd_a, fwd_b, label)
        (1, 2, 0, 0, 0, 0, FWD_NONE, FWD_NONE, "no producer"),
        (1, 2, 1, 1, 0, 0, FWD_MEM,  FWD_NONE, "rs1 from EX/MEM"),
        (1, 2, 1, 2, 0, 0, FWD_NONE, FWD_MEM,  "rs2 from EX/MEM"),
        (1, 2, 0, 0, 1, 1, FWD_WB,   FWD_NONE, "rs1 from MEM/WB"),
        (1, 2, 0, 0, 1, 2, FWD_NONE, FWD_WB,   "rs2 from MEM/WB"),
        (3, 3, 1, 3, 0, 0, FWD_MEM,  FWD_MEM,  "rs1 == rs2, both forwarded"),
        (1, 2, 1, 1, 1, 2, FWD_MEM,  FWD_WB,   "rs1 from MEM, rs2 from WB"),
        (5, 5, 1, 5, 1, 5, FWD_MEM,  FWD_MEM,  "both write the same reg: EX/MEM is newer"),
        (5, 6, 0, 5, 1, 5, FWD_WB,   FWD_NONE, "EX/MEM matches but does not write"),
        (0, 0, 1, 0, 1, 0, FWD_NONE, FWD_NONE, "x0 is never forwarded"),
        (0, 7, 1, 0, 1, 7, FWD_NONE, FWD_WB,   "x0 in EX/MEM does not hide MEM/WB"),
    ]
    for rs1, rs2, emw, emr, mww, mwr, exp_a, exp_b, label in cases:
        a, b = await apply(dut, rs1, rs2, emw, emr, mww, mwr)
        assert (a, b) == (exp_a, exp_b), f"{label}: forward_a={a:02b} forward_b={b:02b}, expected {exp_a:02b} {exp_b:02b}"


@cocotb.test()
async def test_random(dut):
    """Random inputs from a small register range, so matches happen often."""
    for _ in range(2000):
        rs1, rs2, emr, mwr = (random.randint(0, 3) for _ in range(4))
        emw, mww = random.randint(0, 1), random.randint(0, 1)
        a, b = await apply(dut, rs1, rs2, emw, emr, mww, mwr)
        assert a == model(rs1, emw, emr, mww, mwr), f"forward_a wrong for rs1={rs1} ex_mem=({emw},{emr}) mem_wb=({mww},{mwr})"
        assert b == model(rs2, emw, emr, mww, mwr), f"forward_b wrong for rs2={rs2} ex_mem=({emw},{emr}) mem_wb=({mww},{mwr})"