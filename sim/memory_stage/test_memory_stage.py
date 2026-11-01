import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


SB, SH, SW = 0b000, 0b001, 0b010
LB, LH, LW, LBU, LHU = 0b000, 0b001, 0b010, 0b100, 0b101

MASK32 = 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Python reference model: a plain byte array, little endian like RISC-V
# ---------------------------------------------------------------------------

class MemoryModel:
    def __init__(self, size):
        self.mem = bytearray(size)

    def store(self, addr, data, funct3):
        width = {SB: 1, SH: 2, SW: 4}[funct3]
        for i in range(width):
            self.mem[addr + i] = (data >> (8 * i)) & 0xFF

    def load(self, addr, funct3):
        width = {LB: 1, LBU: 1, LH: 2, LHU: 2, LW: 4}[funct3]
        value = int.from_bytes(self.mem[addr:addr + width], "little")
        if funct3 in (LB, LH) and value & (1 << (8 * width - 1)):
            value -= 1 << (8 * width)     # sign-extend
        return value & MASK32


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def mem_ctrl(mem_read=0, mem_write=0):
    """Pack mem_ctrl_t: {mem_read, mem_write}."""
    return (mem_read << 1) | mem_write


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.mem_ctrl.value = 0
    dut.addr.value = 0
    dut.store_data.value = 0
    dut.funct3.value = 0
    await FallingEdge(dut.clk)


async def store(dut, addr, data, funct3):
    """Drive a store on the falling edge, it is written on the next rising edge."""
    # Loads only wait 1 ns, so after several loads the simulation time can sit
    # anywhere in the clock period. Re-align first, otherwise the inputs may
    # change right at a rising edge (race).
    await FallingEdge(dut.clk)
    dut.mem_ctrl.value = mem_ctrl(mem_write=1)
    dut.addr.value = addr
    dut.store_data.value = data & MASK32
    dut.funct3.value = funct3
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.mem_ctrl.value = 0


async def load(dut, addr, funct3):
    """Loads are combinational: set the inputs, let them settle, read the result."""
    dut.mem_ctrl.value = mem_ctrl(mem_read=1)
    dut.addr.value = addr
    dut.funct3.value = funct3
    await Timer(1, unit="ns")
    return int(dut.load_data.value)


async def clear(dut, words):
    """Zero the first words of memory so no X is ever read."""
    for w in range(words):
        await store(dut, 4 * w, 0, SW)


def check(got, expected, label):
    expected &= MASK32
    assert got == expected, f"{label}: 0x{got:08x}, expected 0x{expected:08x}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_word(dut):
    """sw followed by lw returns the same word."""
    await setup(dut)
    await store(dut, 0x10, 0xDEADBEEF, SW)
    check(await load(dut, 0x10, LW), 0xDEADBEEF, "lw after sw")


@cocotb.test()
async def test_store_byte_lanes(dut):
    """sb at each offset changes exactly one byte of the word."""
    await setup(dut)
    await store(dut, 0x20, 0x00000000, SW)
    for offset, byte in enumerate([0x11, 0x22, 0x33, 0x44]):
        await store(dut, 0x20 + offset, byte, SB)
    check(await load(dut, 0x20, LW), 0x44332211, "four sb, little endian")

    # Upper bits of store_data must be ignored
    await store(dut, 0x21, 0xFFFFFFAA, SB)
    check(await load(dut, 0x20, LW), 0x4433AA11, "sb ignores store_data[31:8]")


@cocotb.test()
async def test_store_half_lanes(dut):
    """sh at offset 0 and 2 changes only its halfword."""
    await setup(dut)
    await store(dut, 0x30, 0x00000000, SW)
    await store(dut, 0x30, 0xBEEF, SH)
    await store(dut, 0x32, 0xFFFFDEAD, SH)   # upper bits must be ignored
    check(await load(dut, 0x30, LW), 0xDEADBEEF, "two sh")


@cocotb.test()
async def test_load_extension(dut):
    """lb/lh sign-extend, lbu/lhu zero-extend, at every valid offset."""
    await setup(dut)
    await store(dut, 0x40, 0x7F80FF01, SW)   # bytes: 01, FF, 80, 7F

    expected_bytes = [0x01, 0xFF, 0x80, 0x7F]
    for offset, b in enumerate(expected_bytes):
        signed_b = b - 0x100 if b & 0x80 else b
        check(await load(dut, 0x40 + offset, LB),  signed_b, f"lb  +{offset}")
        check(await load(dut, 0x40 + offset, LBU), b,        f"lbu +{offset}")

    check(await load(dut, 0x40, LH),  0xFFFFFF01, "lh  +0 (0xFF01 is negative)")
    check(await load(dut, 0x40, LHU), 0x0000FF01, "lhu +0")
    check(await load(dut, 0x42, LH),  0x00007F80, "lh  +2 (0x7F80 is positive)")
    check(await load(dut, 0x42, LHU), 0x00007F80, "lhu +2")


@cocotb.test()
async def test_no_write_without_enable(dut):
    """With mem_write = 0 the memory must not change."""
    await setup(dut)
    await store(dut, 0x50, 0x12345678, SW)

    dut.mem_ctrl.value = mem_ctrl(mem_read=1)
    dut.addr.value = 0x50
    dut.store_data.value = 0xFFFFFFFF
    dut.funct3.value = SW
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

    check(await load(dut, 0x50, LW), 0x12345678, "write without mem_write")


@cocotb.test()
async def test_misaligned(dut):
    """misaligned is set for lh/sh on odd addresses and lw/sw not on multiples of 4."""
    await setup(dut)

    cases = [
        # (funct3, offset, misaligned)
        (LB, 0, 0), (LB, 1, 0), (LB, 2, 0), (LB, 3, 0),
        (LH, 0, 0), (LH, 1, 1), (LH, 2, 0), (LH, 3, 1),
        (LHU, 1, 1), (LBU, 3, 0),
        (LW, 0, 0), (LW, 1, 1), (LW, 2, 1), (LW, 3, 1),
    ]
    for funct3, offset, expected in cases:
        for read, write in ((1, 0), (0, 1)):
            if write and funct3 in (LBU, LHU):
                continue                     # there is no sbu / shu
            dut.mem_ctrl.value = mem_ctrl(read, write)
            dut.addr.value = 0x100 + offset
            dut.funct3.value = funct3
            await Timer(1, unit="ns")
            kind = "load" if read else "store"
            got = int(dut.misaligned.value)
            assert got == expected, f"{kind} funct3={funct3:03b} offset={offset}: misaligned={got}, expected {expected}"

    # No memory access -> never misaligned, even for an odd ALU result
    dut.mem_ctrl.value = 0
    dut.addr.value = 0x103
    dut.funct3.value = LW
    await Timer(1, unit="ns")
    assert int(dut.misaligned.value) == 0, "misaligned set without a memory access"


@cocotb.test()
async def test_random(dut):
    """Random aligned loads and stores of all widths against the Python model."""
    await setup(dut)

    words = 32                              # small region -> many overlapping accesses
    model = MemoryModel(4 * words)
    await clear(dut, words)

    for _ in range(1000):
        if random.random() < 0.5:
            funct3 = random.choice((SB, SH, SW))
            align = {SB: 1, SH: 2, SW: 4}[funct3]
            addr = random.randrange(0, 4 * words, align)
            data = random.getrandbits(32)
            await store(dut, addr, data, funct3)
            model.store(addr, data, funct3)
        else:
            funct3 = random.choice((LB, LBU, LH, LHU, LW))
            align = {LB: 1, LBU: 1, LH: 2, LHU: 2, LW: 4}[funct3]
            addr = random.randrange(0, 4 * words, align)
            check(await load(dut, addr, funct3), model.load(addr, funct3),
                  f"funct3={funct3:03b} addr=0x{addr:x}")