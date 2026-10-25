class InstructionMemoryModel:
    def __init__(self, dut, size=1024):
        self.dut = dut
        self.size = size

    def load(self, instructions):
        "Writes instructions into the instruction memory of the processor"
        for addr, instr in enumerate(instructions):
            self.dut.imem_inst.memory[addr].value = instr