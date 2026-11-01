"""Whole-CPU tests: run small programs and check registers and data memory.

Forwarding, the register file bypass and load-use hazard detection are in
place, so programs run without any NOPs.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from helpers.riscv_asm import Program


PADDING = 0
LOAD_PADDING = 0
MASK32 = 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def regs(dut):
    return dut.decode_inst.rf_inst.reg_file


def dmem(dut):
    return dut.memory_inst.dmem_inst.memory


async def run(dut, program, cycles=None, clear_words=64):
    """Reset, load the program, clear registers and data memory, then run.

    Reset comes first: all tests share one simulation, and an access still in
    the pipeline from the previous test must not hit the freshly loaded memory.
    """
    dut.rst_n.value = 0
    await Timer(1, unit="ns")

    words = program.assemble()
    imem = dut.fetch_inst.imem_inst.memory
    for addr, word in enumerate(words):
        imem[addr].value = word

    # Uninitialised memory is X in simulation; start from a clean state
    for i in range(1, 32):
        regs(dut)[i].value = 0
    for i in range(clear_words):
        dmem(dut)[i].value = 0

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    # Every instruction leaves the pipeline at most 5 cycles after it entered
    for _ in range(cycles or len(words) + 10):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")


def reg(dut, n):
    return int(regs(dut)[n].value)


def word(dut, byte_addr):
    return int(dmem(dut)[byte_addr // 4].value)


def check_regs(dut, expected):
    for n, value in expected.items():
        got = reg(dut, n)
        value &= MASK32
        assert got == value, f"x{n} = 0x{got:08x}, expected 0x{value:08x}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_arithmetic(dut):
    """R- and I-type ALU instructions, results checked in the register file."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 5)
    p.addi(2, 0, -3)
    p.add(3, 1, 2)          # 2
    p.sub(4, 1, 2)          # 8
    p.slt(5, 2, 1)          # -3 < 5 -> 1
    p.sltu(6, 2, 1)         # 0xFFFFFFFD < 5 -> 0
    p.xori(7, 1, 0xFF)      # 0xFA
    p.slli(8, 1, 4)         # 80
    p.srai(9, 2, 1)         # -2
    p.srli(10, 2, 28)       # 0xF
    p.and_(11, 1, 2)        # 5 & -3 = 5
    p.or_(12, 1, 2)         # -3
    p.halt()
    await run(dut, p)

    check_regs(dut, {1: 5, 2: -3, 3: 2, 4: 8, 5: 1, 6: 0, 7: 0xFA,
                     8: 80, 9: -2, 10: 0xF, 11: 5, 12: -3})


@cocotb.test()
async def test_x0_stays_zero(dut):
    """Writing x0 has no effect."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(0, 0, 123)
    p.add(1, 0, 0)
    p.halt()
    await run(dut, p)

    # x1 = x0 + x0 goes through the read port, which returns 0 for x0
    check_regs(dut, {1: 0})
    # The array entry for x0 is never written. It stays uninitialised (X)
    # in simulation, which is exactly the point: the 123 never arrived.
    raw = regs(dut)[0].value
    assert not raw.is_resolvable or int(raw) != 123, "addi x0, x0, 123 was written into the register file"


@cocotb.test()
async def test_upper_immediates(dut):
    """lui, auipc and the li pseudo-instruction."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.lui(1, 0x12345)                # 0x12345000
    p.label("auipc")
    p.auipc(2, 0x1)                  # pc of this instruction + 0x1000
    p.li(3, 0xDEADBEEF)              # lui + addi with a negative low part
    p.li(4, -1)
    p.halt()
    await run(dut, p)
    check_regs(dut, {1: 0x12345000, 2: p.labels["auipc"] + 0x1000, 3: 0xDEADBEEF, 4: -1})


@cocotb.test()
async def test_load_store(dut):
    """Stores of all widths, loads with sign and zero extension."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 0x40)               # base address
    p.li(2, 0x80FF7F01)
    p.sw(2, 0, 1)
    p.lw(3, 0, 1)                    # 0x80FF7F01
    p.lb(4, 3, 1)                    # byte 3 = 0x80 -> -128
    p.lbu(5, 3, 1)                   # 0x80
    p.lh(6, 2, 1)                    # 0x80FF -> negative
    p.lhu(7, 2, 1)                   # 0x80FF
    p.addi(8, 0, 0x55)
    p.sb(8, 4, 1)                    # byte at 0x44
    p.sh(8, 6, 1)                    # halfword at 0x46
    p.lw(9, 4, 1)                    # 0x00550055
    p.halt()
    await run(dut, p)

    check_regs(dut, {3: 0x80FF7F01, 4: -128, 5: 0x80, 6: 0xFFFF80FF, 7: 0x80FF, 9: 0x00550055})
    assert word(dut, 0x40) == 0x80FF7F01, "word at 0x40 not stored"
    assert word(dut, 0x44) == 0x00550055, f"word at 0x44 = 0x{word(dut, 0x44):08x}"


@cocotb.test()
async def test_loop(dut):
    """A counting loop with a backward branch: sum 1..10 = 55."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 0)                  # sum
    p.addi(2, 0, 1)                  # i
    p.addi(3, 0, 11)                 # limit
    p.label("loop")
    p.add(1, 1, 2)
    p.addi(2, 2, 1)
    p.blt(2, 3, "loop")
    p.halt()
    await run(dut, p, cycles=300)
    check_regs(dut, {1: 55, 2: 11})


@cocotb.test()
async def test_branches(dut):
    """Every branch type, taken and not taken. x10 counts the taken ones."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, -1)
    p.addi(2, 0, 1)
    p.addi(10, 0, 0)
    for i, (op, a, b, taken) in enumerate([
        ("beq", 1, 1, True), ("beq", 1, 2, False),
        ("bne", 1, 2, True), ("bne", 2, 2, False),
        ("blt", 1, 2, True), ("blt", 2, 1, False),     # signed: -1 < 1
        ("bge", 2, 1, True), ("bge", 1, 2, False),
        ("bltu", 2, 1, True), ("bltu", 1, 2, False),   # unsigned: 1 < 0xFFFFFFFF
        ("bgeu", 1, 2, True), ("bgeu", 2, 1, False),
    ]):
        getattr(p, op)(a, b, f"t{i}")
        p.addi(11 + i, 0, 1)         # only executed if the branch is NOT taken
        p.label(f"t{i}")
        p.addi(10, 10, 1 if taken else 0)
    p.halt()
    await run(dut, p, cycles=400)

    check_regs(dut, {10: 6})
    for i, taken in enumerate([True, False] * 6):
        expected = 0 if taken else 1
        assert reg(dut, 11 + i) == expected, \
            f"branch {i}: x{11 + i} = {reg(dut, 11 + i)}, expected {expected}"


@cocotb.test()
async def test_call_return(dut):
    """jal/jalr as call and return. The two instructions behind a jump are flushed.

    The instructions at 4 and 8 sit behind the jal, so they are fetched and
    flushed once when the call happens, and executed once after the return.
    If the flush did not work, x5 and x6 would end up at 2.
    """
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.jal(1, "func", pad=False)      # 0: call, x1 = 4
    p.addi(5, 5, 1, pad=False)       # 4: flushed on the call, runs after return
    p.addi(6, 6, 1, pad=False)       # 8: same
    p.halt()                         # 12
    p.label("func")
    p.addi(8, 0, 1)
    p.label("ret")
    p.jalr(3, 1, 0, pad=False)       # return to x1, x3 = address of jalr + 4
    p.addi(9, 9, 1, pad=False)       # flushed
    p.addi(9, 9, 1, pad=False)       # flushed
    p.halt()
    await run(dut, p, cycles=60)

    check_regs(dut, {1: 4, 5: 1, 6: 1, 8: 1, 9: 0, 3: p.labels["ret"] + 4})


# ---------------------------------------------------------------------------
# Forwarding: every distance and every consumer of a forwarded value
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_forward_chain(dut):
    """Each instruction uses the result of the one directly before (EX/MEM forwarding)."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 1)
    for _ in range(10):
        p.add(1, 1, 1)               # doubles x1 every time
    p.halt()
    await run(dut, p)
    check_regs(dut, {1: 1 << 10})


@cocotb.test()
async def test_forward_distances(dut):
    """Producer 1, 2 and 3 instructions ahead, on rs1 and on rs2.

    Distance 1 -> EX/MEM, distance 2 -> MEM/WB, distance 3 -> register file bypass.
    """
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    for dist in (1, 2, 3):
        base = 4 * dist + 1                      # x5..x8, x9..x12, x13..x16
        p.addi(base, 0, 100 + dist)              # producer
        for _ in range(dist - 1):
            p.addi(31, 31, 0)                    # unrelated filler
        p.add(base + 1, base, 0)                 # consumer on rs1
        p.addi(base + 2, 0, 200 + dist)          # producer
        for _ in range(dist - 1):
            p.addi(31, 31, 0)
        p.add(base + 3, 0, base + 2)             # consumer on rs2
    p.halt()
    await run(dut, p)
    for dist in (1, 2, 3):
        base = 4 * dist + 1                      # x5..x8, x9..x12, x13..x16
        check_regs(dut, {base + 1: 100 + dist, base + 3: 200 + dist})


@cocotb.test()
async def test_forward_newest_wins(dut):
    """Two writes to the same register in a row: the newer value must be used."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 1)
    p.addi(1, 0, 2)                  # newer, in MEM while the older one is in WB
    p.add(2, 1, 0)
    p.halt()
    await run(dut, p)
    check_regs(dut, {2: 2})


@cocotb.test()
async def test_forward_into_store_and_branch(dut):
    """Forwarded values as store data, store address and branch operands."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 0x80)               # address, used right away
    p.addi(2, 0, 0x5A)               # data, used right away
    p.sw(2, 0, 1)
    p.addi(3, 0, 7)
    p.addi(4, 0, 7)
    p.beq(3, 4, "taken")             # both operands forwarded
    p.addi(5, 0, 1)                  # skipped if forwarding works
    p.label("taken")
    p.halt()
    await run(dut, p)
    assert word(dut, 0x80) == 0x5A, f"word at 0x80 = 0x{word(dut, 0x80):08x}, expected 0x5a"
    check_regs(dut, {5: 0})


@cocotb.test()
async def test_forward_after_load(dut):
    """A load directly followed by a user of its value: one stall, then MEM/WB forwarding."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 0x40)
    p.addi(2, 0, 123)
    p.sw(2, 0, 1)
    p.lw(3, 0, 1)
    p.addi(4, 3, 1)
    p.halt()
    await run(dut, p)
    check_regs(dut, {3: 123, 4: 124})


@cocotb.test()
async def test_forward_link_register(dut):
    """The return address of jal is used right after the jump target."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.jal(1, "target")               # x1 = 4
    p.halt()
    p.label("target")
    p.addi(2, 1, 100)                # needs x1 immediately
    p.halt()
    await run(dut, p)
    check_regs(dut, {1: 4, 2: 104})


# ---------------------------------------------------------------------------
# Load-use hazards
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_load_use_cases(dut):
    """Every way an instruction can use a value loaded directly before it."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 0x40)
    p.addi(2, 0, 0x48)
    p.sw(2, 0, 1)                    # mem[0x40] = 0x48 (also usable as an address)
    p.addi(9, 0, 5)
    p.sw(9, 8, 1)                    # mem[0x48] = 5

    p.lw(3, 0, 1)
    p.addi(4, 3, 1)                  # rs1 depends on the load -> 0x49
    p.lw(5, 0, 1)
    p.add(6, 0, 5)                   # rs2 depends on the load -> 0x48
    p.lw(7, 0, 1)
    p.sw(7, 4, 1)                    # store data depends on the load -> mem[0x44] = 0x48
    p.lw(8, 0, 1)
    p.lw(10, 0, 8)                   # address depends on the load (pointer chasing) -> 5
    p.lw(11, 0, 1)
    p.sw(9, 4, 11)                   # store address depends on the load -> mem[0x4C] = 5
    p.addi(14, 0, 100)
    p.lw(15, 8, 1)
    p.add(14, 14, 15)                # not idempotent: running twice would give 110 -> 105
    p.lw(12, 8, 1)
    p.beq(12, 9, "taken")            # branch operand depends on the load
    p.addi(13, 0, 1)                 # skipped
    p.label("taken")
    p.halt()
    await run(dut, p)

    check_regs(dut, {4: 0x49, 6: 0x48, 10: 5, 13: 0, 14: 105})
    assert word(dut, 0x44) == 0x48, f"word at 0x44 = 0x{word(dut, 0x44):08x}, expected 0x48"
    assert word(dut, 0x4C) == 5, f"word at 0x4C = 0x{word(dut, 0x4C):08x}, expected 5"


@cocotb.test()
async def test_stall_count(dut):
    """Exactly one stall cycle per load-use hazard, and none anywhere else."""
    p = Program(padding=PADDING, load_padding=LOAD_PADDING)
    p.addi(1, 0, 0x40)
    p.addi(2, 0, 7)
    p.sw(2, 0, 1)
    p.lw(3, 0, 1)
    p.add(4, 3, 3)                   # hazard 1
    p.lw(5, 0, 1)
    p.add(6, 2, 2)                   # independent: no stall
    p.add(7, 5, 2)                   # distance 2: forwarded from MEM/WB, no stall
    p.lw(0, 0, 1)
    p.add(8, 0, 0)                   # load into x0: no stall
    p.lw(9, 0, 1)
    p.add(10, 2, 9)                  # hazard 2 (rs2)
    p.lw(11, 0, 1)
    p.sw(11, 4, 1)                   # hazard 3 (store data)
    p.halt()

    stalls = 0

    async def count():
        nonlocal stalls
        while True:
            await FallingEdge(dut.clk)
            if dut.stall.value.is_resolvable and int(dut.stall.value):
                stalls += 1

    cocotb.start_soon(count())
    await run(dut, p)

    check_regs(dut, {4: 14, 6: 14, 7: 14, 10: 14})
    assert word(dut, 0x44) == 7, "store after load-use hazard went wrong"
    assert stalls == 3, f"{stalls} stall cycles, expected exactly 3"