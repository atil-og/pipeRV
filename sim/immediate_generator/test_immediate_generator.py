import cocotb
from cocotb.triggers import Timer


async def setup(dut):
    """Setup immediate generator"""
    dut.instr.value = 0
    await Timer(1, unit="ns")


async def check(dut, instr, expected):
    """Apply an instruction and compare the generated immediate"""
    dut.instr.value = instr
    await Timer(1, unit="ns")
    got = dut.imm.value.to_unsigned()
    expected &= 0xFFFFFFFF
    assert got == expected, f"instr=0x{instr:08x}: imm=0x{got:08x}, expected 0x{expected:08x}"


@cocotb.test()
async def test_i_type(dut):
    """I-Type: addi, lw, jalr"""
    await check(dut, 0x00500093, 5)       # addi x1, x0, 5
    await check(dut, 0xFFF00093, -1)      # addi x1, x0, -1
    await check(dut, 0x7FF00093, 2047)    # addi x1, x0, 2047   (largest positive)
    await check(dut, 0x80000093, -2048)   # addi x1, x0, -2048  (smallest negative)
    await check(dut, 0xFFC02083, -4)      # lw   x1, -4(x0)
    await check(dut, 0x008080E7, 8)       # jalr x1, 8(x1)


@cocotb.test()
async def test_s_type(dut):
    """S-Type: sw"""
    await check(dut, 0x00102423, 8)       # sw x1, 8(x0)
    await check(dut, 0xFE002E23, -4)      # sw x0, -4(x0)


@cocotb.test()
async def test_b_type(dut):
    """B-Type: beq, bne"""
    await check(dut, 0x00000463, 8)       # beq x0, x0, 8
    await check(dut, 0xFE000EE3, -4)      # beq x0, x0, -4
    await check(dut, 0x00209463, 8)       # bne x1, x2, 8


@cocotb.test()
async def test_u_type(dut):
    """U-Type: lui, auipc"""
    await check(dut, 0x123450B7, 0x12345000)  # lui   x1, 0x12345
    await check(dut, 0xFFFFF0B7, 0xFFFFF000)  # lui   x1, 0xFFFFF
    await check(dut, 0x00001097, 0x00001000)  # auipc x1, 0x1


@cocotb.test()
async def test_j_type(dut):
    """J-Type: jal"""
    await check(dut, 0x008000EF, 8)       # jal x1, 8
    await check(dut, 0xFFDFF06F, -4)      # jal x0, -4


@cocotb.test()
async def test_no_immediate(dut):
    """R-Type and SYSTEM have no immediate, output must be 0."""
    await check(dut, 0x002081B3, 0)       # add x3, x1, x2
    await check(dut, 0x40208133, 0)       # sub x2, x1, x2
    await check(dut, 0x00000073, 0)       # ecall

