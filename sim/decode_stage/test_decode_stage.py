import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


# ---------------------------------------------------------------------------
# Constants (must match riscv_pkg.sv)
# ---------------------------------------------------------------------------

ALU_ADD, ALU_SUB, ALU_SLL, ALU_SLT, ALU_SLTU = 0, 1, 2, 3, 4
ALU_XOR, ALU_SRL, ALU_SRA, ALU_OR, ALU_AND = 5, 6, 7, 8, 9
ALU_PASS_B = 10

WB_ALU, WB_MEM, WB_PC4 = 0, 1, 2

MASK32 = 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Instruction encoders
# ---------------------------------------------------------------------------

def r_type(funct7, rs2, rs1, funct3, rd, opcode=0b0110011):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def i_type(imm, rs1, funct3, rd, opcode=0b0010011):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def s_type(imm, rs2, rs1, funct3):
    return (((imm >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15) \
        | (funct3 << 12) | ((imm & 0x1F) << 7) | 0b0100011


def b_type(imm, rs2, rs1, funct3):
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) \
        | (rs1 << 15) | (funct3 << 12) | (((imm >> 1) & 0xF) << 8) \
        | (((imm >> 11) & 1) << 7) | 0b1100011


def u_type(imm, rd, opcode):
    return (imm & 0xFFFFF000) | (rd << 7) | opcode


def j_type(imm, rd):
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) \
        | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | 0b1101111


# ---------------------------------------------------------------------------
# Struct unpacking: packed structs arrive as plain bit vectors, MSB = first field
# ---------------------------------------------------------------------------

def ex_ctrl(dut):
    v = dut.ex_ctrl.value.to_unsigned()
    return {
        "alu_op":    (v >> 5) & 0xF,
        "alu_src_a": (v >> 4) & 1,
        "alu_src_b": (v >> 3) & 1,
        "branch":    (v >> 2) & 1,
        "jump":      (v >> 1) & 1,
        "jalr":      v & 1,
    }


def mem_ctrl(dut):
    v = dut.mem_ctrl.value.to_unsigned()
    return {"mem_read": (v >> 1) & 1, "mem_write": v & 1}


def wb_ctrl(dut):
    v = dut.wb_ctrl.value.to_unsigned()
    return {"reg_write": (v >> 2) & 1, "wb_sel": v & 0b11}


def expected_ctrl(alu_op=0, alu_src_a=0, alu_src_b=0, branch=0, jump=0, jalr=0,
                  mem_read=0, mem_write=0, reg_write=0, wb_sel=0):
    """Everything defaults to 0, so a case only lists the signals it sets."""
    return {
        "alu_op": alu_op, "alu_src_a": alu_src_a, "alu_src_b": alu_src_b,
        "branch": branch, "jump": jump, "jalr": jalr,
        "mem_read": mem_read, "mem_write": mem_write,
        "reg_write": reg_write, "wb_sel": wb_sel,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def setup(dut):
    """Start the clock and drive all inputs to a known state."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.instr.value = 0x00000013  # NOP
    dut.wb_reg_write.value = 0
    dut.wb_rd.value = 0
    dut.wb_data.value = 0
    await FallingEdge(dut.clk)


async def write_reg(dut, rd, data):
    """Write a register through the write-back port."""
    dut.wb_rd.value = rd
    dut.wb_data.value = data
    dut.wb_reg_write.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.wb_reg_write.value = 0


async def decode(dut, instr):
    """Apply an instruction and let the combinational logic settle."""
    dut.instr.value = instr
    await Timer(1, unit="ns")


def check_ctrl(dut, expected, label):
    got = {**ex_ctrl(dut), **mem_ctrl(dut), **wb_ctrl(dut)}
    diff = {k: (got[k], expected[k]) for k in expected if got[k] != expected[k]}
    assert not diff, f"{label}: wrong control signals (got, expected): {diff}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_field_extraction(dut):
    """rs1, rs2, rd and funct3 come out of the right instruction bits."""
    await setup(dut)

    for _ in range(200):
        rs1, rs2, rd = random.getrandbits(5), random.getrandbits(5), random.getrandbits(5)
        funct3 = random.getrandbits(3)
        await decode(dut, r_type(0, rs2, rs1, funct3, rd))

        assert dut.rs1.value.to_unsigned() == rs1, f"rs1 = {dut.rs1.value.to_unsigned()}, expected {rs1}"
        assert dut.rs2.value.to_unsigned() == rs2, f"rs2 = {dut.rs2.value.to_unsigned()}, expected {rs2}"
        assert dut.rd.value.to_unsigned() == rd, f"rd = {dut.rd.value.to_unsigned()}, expected {rd}"
        assert dut.funct3.value.to_unsigned() == funct3, f"funct3 = {dut.funct3.value.to_unsigned()}, expected {funct3}"


@cocotb.test()
async def test_control_signals(dut):
    """Control signals for every instruction type (table in doc/architecture.md)."""
    await setup(dut)

    cases = [
        # R-type
        ("add",   r_type(0x00, 2, 1, 0b000, 3), expected_ctrl(alu_op=ALU_ADD,  reg_write=1, wb_sel=WB_ALU)),
        ("sub",   r_type(0x20, 2, 1, 0b000, 3), expected_ctrl(alu_op=ALU_SUB,  reg_write=1, wb_sel=WB_ALU)),
        ("sll",   r_type(0x00, 2, 1, 0b001, 3), expected_ctrl(alu_op=ALU_SLL,  reg_write=1, wb_sel=WB_ALU)),
        ("slt",   r_type(0x00, 2, 1, 0b010, 3), expected_ctrl(alu_op=ALU_SLT,  reg_write=1, wb_sel=WB_ALU)),
        ("sltu",  r_type(0x00, 2, 1, 0b011, 3), expected_ctrl(alu_op=ALU_SLTU, reg_write=1, wb_sel=WB_ALU)),
        ("xor",   r_type(0x00, 2, 1, 0b100, 3), expected_ctrl(alu_op=ALU_XOR,  reg_write=1, wb_sel=WB_ALU)),
        ("srl",   r_type(0x00, 2, 1, 0b101, 3), expected_ctrl(alu_op=ALU_SRL,  reg_write=1, wb_sel=WB_ALU)),
        ("sra",   r_type(0x20, 2, 1, 0b101, 3), expected_ctrl(alu_op=ALU_SRA,  reg_write=1, wb_sel=WB_ALU)),
        ("or",    r_type(0x00, 2, 1, 0b110, 3), expected_ctrl(alu_op=ALU_OR,   reg_write=1, wb_sel=WB_ALU)),
        ("and",   r_type(0x00, 2, 1, 0b111, 3), expected_ctrl(alu_op=ALU_AND,  reg_write=1, wb_sel=WB_ALU)),

        # I-type arithmetic
        ("addi",  i_type(5, 1, 0b000, 3),      expected_ctrl(alu_op=ALU_ADD, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),
        # Negative immediate sets bit 30, must still be ADD (there is no subi)
        ("addi -1", i_type(-1, 1, 0b000, 3),   expected_ctrl(alu_op=ALU_ADD, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),
        ("andi",  i_type(5, 1, 0b111, 3),      expected_ctrl(alu_op=ALU_AND, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),
        ("slli",  i_type(3, 1, 0b001, 3),      expected_ctrl(alu_op=ALU_SLL, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),
        ("srli",  i_type(3, 1, 0b101, 3),      expected_ctrl(alu_op=ALU_SRL, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),
        ("srai",  i_type(0x400 | 3, 1, 0b101, 3), expected_ctrl(alu_op=ALU_SRA, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),

        # Memory
        ("lw",    i_type(8, 1, 0b010, 3, opcode=0b0000011),
                  expected_ctrl(alu_op=ALU_ADD, alu_src_b=1, mem_read=1, reg_write=1, wb_sel=WB_MEM)),
        ("sw",    s_type(8, 2, 1, 0b010),
                  expected_ctrl(alu_op=ALU_ADD, alu_src_b=1, mem_write=1)),

        # Control flow
        ("beq",   b_type(8, 2, 1, 0b000),      expected_ctrl(alu_op=ALU_SUB, branch=1)),
        ("bne",   b_type(-4, 2, 1, 0b001),     expected_ctrl(alu_op=ALU_SUB, branch=1)),
        ("jal",   j_type(16, 1),               expected_ctrl(jump=1, reg_write=1, wb_sel=WB_PC4)),
        ("jalr",  i_type(4, 1, 0b000, 3, opcode=0b1100111),
                  expected_ctrl(alu_op=ALU_ADD, alu_src_b=1, jalr=1, reg_write=1, wb_sel=WB_PC4)),

        # Upper immediates
        ("lui",   u_type(0x12345000, 3, 0b0110111),
                  expected_ctrl(alu_op=ALU_PASS_B, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),
        ("auipc", u_type(0x00001000, 3, 0b0010111),
                  expected_ctrl(alu_op=ALU_ADD, alu_src_a=1, alu_src_b=1, reg_write=1, wb_sel=WB_ALU)),

        # No effect -> everything 0
        ("ecall", 0x00000073, expected_ctrl()),
        ("fence", 0x0000000F, expected_ctrl()),
        ("illegal", 0x00000000, expected_ctrl()),
    ]

    for label, instr, expected in cases:
        await decode(dut, instr)
        check_ctrl(dut, expected, label)


@cocotb.test()
async def test_immediate_wiring(dut):
    """Spot check that the immediate generator is wired through."""
    await setup(dut)

    cases = [
        ("addi -1", i_type(-1, 1, 0b000, 3), -1),
        ("sw 8",    s_type(8, 2, 1, 0b010), 8),
        ("beq -4",  b_type(-4, 2, 1, 0b000), -4),
        ("lui",     u_type(0x12345000, 3, 0b0110111), 0x12345000),
        ("jal 16",  j_type(16, 1), 16),
        ("add",     r_type(0, 2, 1, 0b000, 3), 0),
    ]
    for label, instr, expected in cases:
        await decode(dut, instr)
        got = dut.imm.value.to_unsigned()
        assert got == expected & MASK32, f"{label}: imm = 0x{got:08x}, expected 0x{expected & MASK32:08x}"


@cocotb.test()
async def test_register_read(dut):
    """Values written through the WB port are read back via rs1/rs2 of an instruction."""
    await setup(dut)

    values = {r: random.getrandbits(32) for r in range(1, 32)}
    for r, v in values.items():
        await write_reg(dut, r, v)

    for _ in range(200):
        rs1, rs2 = random.randint(1, 31), random.randint(1, 31)
        await decode(dut, r_type(0, rs2, rs1, 0b000, 5))
        d1, d2 = dut.rs1_data.value.to_unsigned(), dut.rs2_data.value.to_unsigned()
        assert d1 == values[rs1], f"x{rs1}: rs1_data = 0x{d1:08x}, expected 0x{values[rs1]:08x}"
        assert d2 == values[rs2], f"x{rs2}: rs2_data = 0x{d2:08x}, expected 0x{values[rs2]:08x}"


@cocotb.test()
async def test_x0_and_write_enable(dut):
    """x0 always reads 0, and nothing is written while wb_reg_write is 0."""
    await setup(dut)

    await write_reg(dut, 0, 0xDEADBEEF)
    await write_reg(dut, 7, 0x12345678)

    # Attempted write with enable off
    dut.wb_rd.value = 7
    dut.wb_data.value = 0xFFFFFFFF
    dut.wb_reg_write.value = 0
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    await decode(dut, r_type(0, 7, 0, 0b000, 1))  # add x1, x0, x7
    assert dut.rs1_data.value.to_unsigned() == 0, "x0 is not 0"
    assert dut.rs2_data.value.to_unsigned() == 0x12345678, "x7 was overwritten although wb_reg_write = 0"