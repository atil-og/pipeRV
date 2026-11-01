import random

import cocotb
from cocotb.triggers import Timer


def model(mem_read, rd, rs1, rs2):
    return int(bool(mem_read) and rd != 0 and (rd == rs1 or rd == rs2))


async def apply(dut, mem_read, rd, rs1, rs2):
    dut.id_ex_mem_read.value = mem_read
    dut.id_ex_rd.value = rd
    dut.id_rs1.value = rs1
    dut.id_rs2.value = rs2
    await Timer(1, unit="ns")
    return int(dut.load_use_stall.value)


@cocotb.test()
async def test_directed(dut):
    cases = [
        # (mem_read, rd, rs1, rs2, stall, label)
        (1, 5, 5, 0, 1, "load rd == rs1"),
        (1, 5, 0, 5, 1, "load rd == rs2"),
        (1, 5, 5, 5, 1, "load rd == rs1 == rs2"),
        (1, 5, 6, 7, 0, "load, no dependency"),
        (0, 5, 5, 5, 0, "not a load (ALU result is forwarded)"),
        (1, 0, 0, 0, 0, "load into x0 never stalls"),
    ]
    for mem_read, rd, rs1, rs2, expected, label in cases:
        got = await apply(dut, mem_read, rd, rs1, rs2)
        assert got == expected, f"{label}: load_use_stall = {got}, expected {expected}"


@cocotb.test()
async def test_random(dut):
    for _ in range(2000):
        mem_read = random.randint(0, 1)
        rd, rs1, rs2 = (random.randint(0, 3) for _ in range(3))
        got = await apply(dut, mem_read, rd, rs1, rs2)
        assert got == model(mem_read, rd, rs1, rs2), \
            f"mem_read={mem_read} rd={rd} rs1={rs1} rs2={rs2}: load_use_stall = {got}"