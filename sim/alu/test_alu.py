import random

import cocotb
from cocotb.triggers import Timer


# Must match riscv_pkg.sv
ALU_ADD, ALU_SUB, ALU_SLL, ALU_SLT, ALU_SLTU = 0, 1, 2, 3, 4
ALU_XOR, ALU_SRL, ALU_SRA, ALU_OR, ALU_AND = 5, 6, 7, 8, 9
ALU_PASS_B = 10

ALL_OPS = [ALU_ADD, ALU_SUB, ALU_SLL, ALU_SLT, ALU_SLTU,
           ALU_XOR, ALU_SRL, ALU_SRA, ALU_OR, ALU_AND, ALU_PASS_B]

MASK32 = 0xFFFFFFFF


def signed(x):
    """Interpret a 32-bit value as two's complement."""
    return x - (1 << 32) if x & 0x80000000 else x


def alu_model(op, a, b):
    """Python reference model of the ALU."""
    shamt = b & 0x1F
    if op == ALU_ADD:
        return (a + b) & MASK32
    if op == ALU_SUB:
        return (a - b) & MASK32
    if op == ALU_SLL:
        return (a << shamt) & MASK32
    if op == ALU_SLT:
        return int(signed(a) < signed(b))
    if op == ALU_SLTU:
        return int(a < b)
    if op == ALU_XOR:
        return a ^ b
    if op == ALU_SRL:
        return a >> shamt
    if op == ALU_SRA:
        return (signed(a) >> shamt) & MASK32
    if op == ALU_OR:
        return a | b
    if op == ALU_AND:
        return a & b
    if op == ALU_PASS_B:
        return b
    return 0


async def check(dut, op, a, b):
    dut.alu_op.value = op
    dut.a.value = a
    dut.b.value = b
    await Timer(1, unit="ns")
    got = dut.result.value.to_unsigned()
    expected = alu_model(op, a, b)
    assert got == expected, (
        f"op={op} a=0x{a:08x} b=0x{b:08x}: result=0x{got:08x}, expected 0x{expected:08x}"
    )


@cocotb.test()
async def test_edge_cases(dut):
    """Values where signed/unsigned handling and overflow usually go wrong."""
    edges = [0, 1, 2, 31, 32, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x0000001F, 0x00000020]
    for op in ALL_OPS:
        for a in edges:
            for b in edges:
                await check(dut, op, a, b)


@cocotb.test()
async def test_known_values(dut):
    """A few hand-checked results, independent of the Python model."""
    cases = [
        (ALU_ADD,  0xFFFFFFFF, 1,          0x00000000),  # overflow wraps
        (ALU_SUB,  0,          1,          0xFFFFFFFF),  # 0 - 1 = -1
        (ALU_SLT,  0xFFFFFFFF, 1,          1),           # -1 < 1 signed
        (ALU_SLTU, 0xFFFFFFFF, 1,          0),           # 0xFFFFFFFF > 1 unsigned
        (ALU_SRA,  0x80000000, 4,          0xF8000000),  # sign bit is copied
        (ALU_SRL,  0x80000000, 4,          0x08000000),  # zeros shifted in
        (ALU_SLL,  1,          0x21,       2),           # only b[4:0] counts: 0x21 -> 1
        (ALU_PASS_B, 0x12345678, 0xCAFE0000, 0xCAFE0000),
    ]
    for op, a, b, expected in cases:
        dut.alu_op.value = op
        dut.a.value = a
        dut.b.value = b
        await Timer(1, unit="ns")
        got = dut.result.value.to_unsigned()
        assert got == expected, f"op={op} a=0x{a:08x} b=0x{b:08x}: 0x{got:08x}, expected 0x{expected:08x}"


@cocotb.test()
async def test_random(dut):
    """Random operands for every operation, compared against the model."""
    for _ in range(2000):
        await check(dut, random.choice(ALL_OPS), random.getrandbits(32), random.getrandbits(32))