"""Minimal RV32I assembler for writing test programs in Python.

    p = Program()
    p.addi(1, 0, 5)
    p.label("loop")
    p.addi(1, 1, -1)
    p.bne(1, 0, "loop")
    words = p.assemble()

Branch and jump targets can be labels or byte offsets. With padding > 0 every
instruction is followed by that many NOPs, so a program runs correctly on a
pipeline without forwarding. load_padding adds NOPs after loads only, for a
pipeline with forwarding but without load-use hazard detection.
"""

NOP = 0x00000013  # addi x0, x0, 0


# ---------------------------------------------------------------------------
# Encoders for the six instruction formats
# ---------------------------------------------------------------------------

def r_type(funct7, rs2, rs1, funct3, rd, opcode):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def i_type(imm, rs1, funct3, rd, opcode):
    assert -2048 <= imm <= 4095, f"I-immediate {imm} out of range"
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def s_type(imm, rs2, rs1, funct3):
    assert -2048 <= imm <= 2047, f"S-immediate {imm} out of range"
    return (((imm >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15) \
        | (funct3 << 12) | ((imm & 0x1F) << 7) | 0b0100011


def b_type(imm, rs2, rs1, funct3):
    assert imm % 2 == 0 and -4096 <= imm <= 4094, f"B-offset {imm} invalid"
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) \
        | (rs1 << 15) | (funct3 << 12) | (((imm >> 1) & 0xF) << 8) \
        | (((imm >> 11) & 1) << 7) | 0b1100011


def u_type(imm20, rd, opcode):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | opcode


def j_type(imm, rd):
    assert imm % 2 == 0 and -(1 << 20) <= imm < (1 << 20), f"J-offset {imm} invalid"
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) \
        | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | 0b1101111


# ---------------------------------------------------------------------------
# Program builder
# ---------------------------------------------------------------------------

class Program:
    def __init__(self, padding=0, load_padding=0):
        self.padding = padding
        self.load_padding = load_padding
        self.items = []           # ints, or functions (pc, labels) -> int
        self.labels = {}

    # -- infrastructure ------------------------------------------------------

    def label(self, name):
        self.labels[name] = 4 * len(self.items)

    def _emit(self, item, pad=True):
        self.items.append(item)
        if pad:
            self.items.extend([NOP] * self.padding)

    def _offset(self, target, pc, labels):
        return labels[target] - pc if isinstance(target, str) else target

    def word(self, value):
        """Raw 32-bit word without padding."""
        self._emit(value, pad=False)

    def assemble(self):
        return [item(4 * i, self.labels) if callable(item) else item
                for i, item in enumerate(self.items)]

    # -- R-type --------------------------------------------------------------

    def _r(self, funct7, funct3, rd, rs1, rs2, pad=True):
        self._emit(r_type(funct7, rs2, rs1, funct3, rd, 0b0110011), pad)

    def add(self, rd, rs1, rs2, pad=True):  self._r(0x00, 0b000, rd, rs1, rs2, pad)
    def sub(self, rd, rs1, rs2, pad=True):  self._r(0x20, 0b000, rd, rs1, rs2, pad)
    def sll(self, rd, rs1, rs2, pad=True):  self._r(0x00, 0b001, rd, rs1, rs2, pad)
    def slt(self, rd, rs1, rs2, pad=True):  self._r(0x00, 0b010, rd, rs1, rs2, pad)
    def sltu(self, rd, rs1, rs2, pad=True): self._r(0x00, 0b011, rd, rs1, rs2, pad)
    def xor(self, rd, rs1, rs2, pad=True):  self._r(0x00, 0b100, rd, rs1, rs2, pad)
    def srl(self, rd, rs1, rs2, pad=True):  self._r(0x00, 0b101, rd, rs1, rs2, pad)
    def sra(self, rd, rs1, rs2, pad=True):  self._r(0x20, 0b101, rd, rs1, rs2, pad)
    def or_(self, rd, rs1, rs2, pad=True):  self._r(0x00, 0b110, rd, rs1, rs2, pad)
    def and_(self, rd, rs1, rs2, pad=True): self._r(0x00, 0b111, rd, rs1, rs2, pad)

    # -- I-type arithmetic ---------------------------------------------------

    def _i(self, funct3, rd, rs1, imm, pad=True, opcode=0b0010011):
        self._emit(i_type(imm, rs1, funct3, rd, opcode), pad)

    def addi(self, rd, rs1, imm, pad=True):  self._i(0b000, rd, rs1, imm, pad)
    def slti(self, rd, rs1, imm, pad=True):  self._i(0b010, rd, rs1, imm, pad)
    def sltiu(self, rd, rs1, imm, pad=True): self._i(0b011, rd, rs1, imm, pad)
    def xori(self, rd, rs1, imm, pad=True):  self._i(0b100, rd, rs1, imm, pad)
    def ori(self, rd, rs1, imm, pad=True):   self._i(0b110, rd, rs1, imm, pad)
    def andi(self, rd, rs1, imm, pad=True):  self._i(0b111, rd, rs1, imm, pad)
    def slli(self, rd, rs1, sh, pad=True):   self._i(0b001, rd, rs1, sh, pad)
    def srli(self, rd, rs1, sh, pad=True):   self._i(0b101, rd, rs1, sh, pad)
    def srai(self, rd, rs1, sh, pad=True):   self._i(0b101, rd, rs1, 0x400 | sh, pad)

    def nop(self):
        self._emit(NOP, pad=False)

    # -- loads and stores ----------------------------------------------------

    def _load(self, funct3, rd, imm, rs1, pad=True):
        self._i(funct3, rd, rs1, imm, pad, opcode=0b0000011)
        if pad:
            self.items.extend([NOP] * self.load_padding)

    def lb(self, rd, imm, rs1, pad=True):  self._load(0b000, rd, imm, rs1, pad)
    def lh(self, rd, imm, rs1, pad=True):  self._load(0b001, rd, imm, rs1, pad)
    def lw(self, rd, imm, rs1, pad=True):  self._load(0b010, rd, imm, rs1, pad)
    def lbu(self, rd, imm, rs1, pad=True): self._load(0b100, rd, imm, rs1, pad)
    def lhu(self, rd, imm, rs1, pad=True): self._load(0b101, rd, imm, rs1, pad)

    def sb(self, rs2, imm, rs1, pad=True): self._emit(s_type(imm, rs2, rs1, 0b000), pad)
    def sh(self, rs2, imm, rs1, pad=True): self._emit(s_type(imm, rs2, rs1, 0b001), pad)
    def sw(self, rs2, imm, rs1, pad=True): self._emit(s_type(imm, rs2, rs1, 0b010), pad)

    # -- control flow --------------------------------------------------------

    def _branch(self, funct3, rs1, rs2, target, pad=True):
        self._emit(lambda pc, labels: b_type(self._offset(target, pc, labels), rs2, rs1, funct3), pad)

    def beq(self, rs1, rs2, target, pad=True):  self._branch(0b000, rs1, rs2, target, pad)
    def bne(self, rs1, rs2, target, pad=True):  self._branch(0b001, rs1, rs2, target, pad)
    def blt(self, rs1, rs2, target, pad=True):  self._branch(0b100, rs1, rs2, target, pad)
    def bge(self, rs1, rs2, target, pad=True):  self._branch(0b101, rs1, rs2, target, pad)
    def bltu(self, rs1, rs2, target, pad=True): self._branch(0b110, rs1, rs2, target, pad)
    def bgeu(self, rs1, rs2, target, pad=True): self._branch(0b111, rs1, rs2, target, pad)

    def jal(self, rd, target, pad=True):
        self._emit(lambda pc, labels: j_type(self._offset(target, pc, labels), rd), pad)

    def jalr(self, rd, rs1, imm, pad=True):
        self._i(0b000, rd, rs1, imm, pad, opcode=0b1100111)

    def halt(self):
        """Endless loop on itself: jal x0, 0."""
        self._emit(j_type(0, 0), pad=False)

    # -- upper immediates ----------------------------------------------------

    def lui(self, rd, imm20, pad=True):   self._emit(u_type(imm20, rd, 0b0110111), pad)
    def auipc(self, rd, imm20, pad=True): self._emit(u_type(imm20, rd, 0b0010111), pad)

    def li(self, rd, value, pad=True):
        """Load any 32-bit constant (lui + addi, like the assembler pseudo-instruction)."""
        value &= 0xFFFFFFFF
        low = value & 0xFFF
        if low >= 0x800:
            low -= 0x1000                   # addi sign-extends, compensate in the upper part
        upper = ((value - low) >> 12) & 0xFFFFF
        if upper:
            self.lui(rd, upper, pad)
            if low:
                self.addi(rd, rd, low, pad)
        else:
            self.addi(rd, 0, low, pad)