import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def setup(dut):
    """Clock starten und alle Eingänge in einen definierten Zustand bringen."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.w_en.value = 0
    dut.write_destination.value = 0
    dut.write_data.value = 0
    dut.addr_reg_1.value = 0
    dut.addr_reg_2.value = 0
    await FallingEdge(dut.clk)


async def write_reg(dut, addr, data, w_en=1):
    """Eingänge auf der fallenden Flanke setzen, Schreiben passiert auf der steigenden."""
    dut.write_destination.value = addr
    dut.write_data.value = data
    dut.w_en.value = w_en
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.w_en.value = 0


async def read_regs(dut, addr1, addr2):
    """Lesen ist kombinatorisch: Adressen setzen, kurz warten, Werte zurückgeben."""
    dut.addr_reg_1.value = addr1
    dut.addr_reg_2.value = addr2
    await Timer(1, unit="ns")
    return dut.data_reg1.value.to_unsigned(), dut.data_reg2.value.to_unsigned()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_x0_is_zero(dut):
    """x0 liefert immer 0, auch nach einem Schreibversuch."""
    await setup(dut)

    await write_reg(dut, 0, 0xDEADBEEF)
    d1, d2 = await read_regs(dut, 0, 0)

    assert d1 == 0, f"x0 auf Port 1 ist 0x{d1:08x}, erwartet 0"
    assert d2 == 0, f"x0 auf Port 2 ist 0x{d2:08x}, erwartet 0"


@cocotb.test()
async def test_write_read_all_regs(dut):
    """Jedes Register x1..x31 beschreiben und über beide Ports zurücklesen."""
    await setup(dut)

    expected = {addr: random.getrandbits(32) for addr in range(1, 32)}
    for addr, data in expected.items():
        await write_reg(dut, addr, data)

    for addr, data in expected.items():
        d1, d2 = await read_regs(dut, addr, addr)
        assert d1 == data, f"x{addr} Port 1: 0x{d1:08x}, erwartet 0x{data:08x}"
        assert d2 == data, f"x{addr} Port 2: 0x{d2:08x}, erwartet 0x{data:08x}"


@cocotb.test()
async def test_no_write_without_enable(dut):
    """Bei w_en = 0 darf sich der Registerinhalt nicht ändern."""
    await setup(dut)

    await write_reg(dut, 5, 0x12345678)
    await write_reg(dut, 5, 0xFFFFFFFF, w_en=0)
    d1, _ = await read_regs(dut, 5, 0)

    assert d1 == 0x12345678, f"x5 ist 0x{d1:08x}, wurde trotz w_en = 0 überschrieben"


@cocotb.test()
async def test_dual_port_read(dut):
    """Beide Ports lesen gleichzeitig unterschiedliche Register."""
    await setup(dut)

    await write_reg(dut, 1, 0x11111111)
    await write_reg(dut, 2, 0x22222222)
    d1, d2 = await read_regs(dut, 1, 2)

    assert d1 == 0x11111111, f"Port 1: 0x{d1:08x}"
    assert d2 == 0x22222222, f"Port 2: 0x{d2:08x}"


@cocotb.test()
async def test_random(dut):
    """Zufällige Schreib- und Lesezugriffe gegen ein Python-Referenzmodell."""
    await setup(dut)

    # Erst alle Register initialisieren, damit nie X gelesen wird
    model = {0: 0}
    for addr in range(1, 32):
        model[addr] = 0
        await write_reg(dut, addr, 0)

    for _ in range(500):
        addr = random.randint(0, 31)
        data = random.getrandbits(32)
        w_en = random.randint(0, 1)
        await write_reg(dut, addr, data, w_en)
        if w_en and addr != 0:
            model[addr] = data

        a1, a2 = random.randint(0, 31), random.randint(0, 31)
        d1, d2 = await read_regs(dut, a1, a2)
        assert d1 == model[a1], f"x{a1} Port 1: 0x{d1:08x}, erwartet 0x{model[a1]:08x}"
        assert d2 == model[a2], f"x{a2} Port 2: 0x{d2:08x}, erwartet 0x{model[a2]:08x}"


@cocotb.test()
async def test_write_read_bypass(dut):
    """Lesen im selben Takt wie Schreiben liefert schon den neuen Wert."""
    await setup(dut)

    await write_reg(dut, 7, 0xAAAAAAAA)

    dut.write_destination.value = 7
    dut.write_data.value = 0x55555555
    dut.w_en.value = 1
    d1, d2 = await read_regs(dut, 7, 7)

    assert d1 == 0x55555555, f"Port 1 ohne Bypass: 0x{d1:08x}"
    assert d2 == 0x55555555, f"Port 2 ohne Bypass: 0x{d2:08x}"