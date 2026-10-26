class InstructionMemoryModel:
    def __init__(self, memory, size=1024):
        """memory: cocotb handle to the memory array, e.g. dut.memory"""
        self.memory = memory
        self.size = size

    def load(self, instructions):
        """Writes instructions into the instruction memory, starting at address 0."""
        if len(instructions) > self.size:
            raise ValueError(f"{len(instructions)} instructions do not fit into {self.size} words")
        for addr, instr in enumerate(instructions):
            self.memory[addr].value = instr