import random

import cocotb
from cocotb.triggers import Timer


# Must match riscv_pkg.sv
ALU_ADD, ALU_SUB, ALU_PASS_B = 0, 1, 10

FWD_NONE, FWD_WB, FWD_MEM = 0b00, 0b01, 0b10

BEQ, BNE, BLT, BGE, BLTU, BGEU = 0b000, 0b001, 0b100, 0b101, 0b110, 0b111

MASK32 = 0xFFFFFFFF


def signed(x):
    return x - (1 << 32) if x & 0x80000000 else x


def pack_ex_ctrl(alu_op=0, alu_src_a=0, alu_src_b=0, branch=0, jump=0, jalr=0):
    """Pack ex_ctrl_t into a bit vector, first struct field = highest bits."""
    return (alu_op << 5) | (alu_src_a << 4) | (alu_src_b << 3) | (branch << 2) | (jump << 1) | jalr


def branch_model(funct3, a, b):
    return {
        BEQ:  a == b,
        BNE:  a != b,
        BLT:  signed(a) < signed(b),
        BGE:  signed(a) >= signed(b),
        BLTU: a < b,
        BGEU: a >= b,
    }[funct3]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def apply(dut, ctrl=0, pc=0, rs1=0, rs2=0, imm=0, funct3=0,
                forward_a=FWD_NONE, forward_b=FWD_NONE, ex_mem_result=0, wb_data=0):
    """Drive every input (unused ones default to 0) and let the logic settle."""
    dut.ex_ctrl.value = ctrl
    dut.pc.value = pc
    dut.rs1_data.value = rs1
    dut.rs2_data.value = rs2
    dut.imm.value = imm & MASK32
    dut.funct3.value = funct3
    dut.forward_a.value = forward_a
    dut.forward_b.value = forward_b
    dut.ex_mem_result.value = ex_mem_result
    dut.wb_data.value = wb_data
    await Timer(1, unit="ns")


def get(dut, name):
    # int() works for 1-bit signals (Logic) and vectors (LogicArray) alike,
    # .to_unsigned() only exists on LogicArray
    return int(getattr(dut, name).value)


def expect(dut, label, **expected):
    for name, value in expected.items():
        got = get(dut, name)
        value &= MASK32
        assert got == value, f"{label}: {name} = 0x{got:08x}, expected 0x{value:08x}"


# ---------------------------------------------------------------------------
# Operand selection
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_r_type(dut):
    """add: rs1 + rs2."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD), rs1=7, rs2=5)
    expect(dut, "add", alu_result=12, pc_sel=0)


@cocotb.test()
async def test_i_type(dut):
    """addi: rs1 + imm, rs2 is ignored."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD, alu_src_b=1), rs1=7, rs2=1000, imm=-3)
    expect(dut, "addi", alu_result=4, pc_sel=0)


@cocotb.test()
async def test_auipc(dut):
    """auipc: pc + imm."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD, alu_src_a=1, alu_src_b=1),
                pc=0x100, rs1=0xDEAD, imm=0x00002000)
    expect(dut, "auipc", alu_result=0x2100, pc_sel=0)


@cocotb.test()
async def test_lui(dut):
    """lui: result = imm."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_PASS_B, alu_src_b=1), rs1=0xDEAD, imm=0x12345000)
    expect(dut, "lui", alu_result=0x12345000, pc_sel=0)


@cocotb.test()
async def test_store_and_pc_plus4(dut):
    """sw: address = rs1 + imm, store_data = rs2. pc_plus4 is always pc + 4."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD, alu_src_b=1),
                pc=0x40, rs1=0x1000, rs2=0xCAFEBABE, imm=8)
    expect(dut, "sw", alu_result=0x1008, store_data=0xCAFEBABE, pc_plus4=0x44, pc_sel=0)


# ---------------------------------------------------------------------------
# Branches and jumps
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_branches(dut):
    """All six branch conditions with edge values and random operands."""
    edges = [0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
    pairs = [(a, b) for a in edges for b in edges]
    pairs += [(random.getrandbits(32), random.getrandbits(32)) for _ in range(200)]

    for funct3 in (BEQ, BNE, BLT, BGE, BLTU, BGEU):
        for a, b in pairs:
            pc = random.getrandbits(30) << 2
            imm = random.randint(-2048, 2047) * 2
            await apply(dut, pack_ex_ctrl(alu_op=ALU_SUB, branch=1),
                        pc=pc, rs1=a, rs2=b, imm=imm, funct3=funct3)

            taken = branch_model(funct3, a, b)
            label = f"funct3={funct3:03b} rs1=0x{a:08x} rs2=0x{b:08x}"
            assert get(dut, "pc_sel") == taken, f"{label}: pc_sel = {get(dut, 'pc_sel')}, expected {int(taken)}"
            if taken:
                expect(dut, label, pc_target=pc + imm)


@cocotb.test()
async def test_no_branch_without_flag(dut):
    """A true condition must not redirect the PC when branch = 0 (e.g. an add with funct3 = 000)."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD), rs1=5, rs2=5, funct3=BEQ)
    expect(dut, "add with equal operands", pc_sel=0)


@cocotb.test()
async def test_undefined_branch_funct3(dut):
    """funct3 = 010 and 011 are not branch conditions and must never be taken."""
    for funct3 in (0b010, 0b011):
        await apply(dut, pack_ex_ctrl(alu_op=ALU_SUB, branch=1), rs1=0, rs2=0, funct3=funct3)
        expect(dut, f"funct3={funct3:03b}", pc_sel=0)


@cocotb.test()
async def test_jal(dut):
    """jal: always taken, target = pc + imm, rd = pc + 4."""
    await apply(dut, pack_ex_ctrl(jump=1), pc=0x200, imm=-8)
    expect(dut, "jal", pc_sel=1, pc_target=0x1F8, pc_plus4=0x204)


@cocotb.test()
async def test_jalr(dut):
    """jalr: target = (rs1 + imm) with bit 0 cleared."""
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD, alu_src_b=1, jalr=1), pc=0x200, rs1=0x1001, imm=4)
    expect(dut, "jalr", pc_sel=1, pc_target=0x1004, pc_plus4=0x204)


# ---------------------------------------------------------------------------
# Forwarding
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_forwarding(dut):
    """Forwarded values replace rs1/rs2 for the ALU, the store data and the branch compare."""
    add = pack_ex_ctrl(alu_op=ALU_ADD)
    stale1, stale2, mem, wb = 0x1, 0x2, 0x100, 0x2000

    await apply(dut, add, rs1=stale1, rs2=stale2, forward_a=FWD_MEM, ex_mem_result=mem, wb_data=wb)
    expect(dut, "fwd a from EX/MEM", alu_result=mem + stale2)

    await apply(dut, add, rs1=stale1, rs2=stale2, forward_a=FWD_WB, ex_mem_result=mem, wb_data=wb)
    expect(dut, "fwd a from MEM/WB", alu_result=wb + stale2)

    await apply(dut, add, rs1=stale1, rs2=stale2, forward_b=FWD_MEM, ex_mem_result=mem, wb_data=wb)
    expect(dut, "fwd b from EX/MEM", alu_result=stale1 + mem, store_data=mem)

    await apply(dut, add, rs1=stale1, rs2=stale2, forward_b=FWD_WB, ex_mem_result=mem, wb_data=wb)
    expect(dut, "fwd b from MEM/WB", alu_result=stale1 + wb, store_data=wb)

    await apply(dut, add, rs1=stale1, rs2=stale2,
                forward_a=FWD_MEM, forward_b=FWD_WB, ex_mem_result=mem, wb_data=wb)
    expect(dut, "fwd both", alu_result=mem + wb)

    # Branch compares the forwarded value: stale rs1 != rs2, forwarded rs1 == rs2
    await apply(dut, pack_ex_ctrl(alu_op=ALU_SUB, branch=1), pc=0x40, rs1=1, rs2=7, imm=16,
                funct3=BEQ, forward_a=FWD_MEM, ex_mem_result=7)
    expect(dut, "beq with forwarded rs1", pc_sel=1, pc_target=0x50)

    # Forwarding must not affect operand a when it is the PC (auipc)
    await apply(dut, pack_ex_ctrl(alu_op=ALU_ADD, alu_src_a=1, alu_src_b=1), pc=0x100, imm=0x1000,
                forward_a=FWD_MEM, ex_mem_result=0xDEAD0000)
    expect(dut, "auipc with forward_a set", alu_result=0x1100)