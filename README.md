# pipeRV

[![tests](https://github.com/atil-og/pipeRV/actions/workflows/tests.yml/badge.svg)](https://github.com/atil-og/pipeRV/actions/workflows/tests.yml)

A 5-stage pipelined RISC-V processor (RV32I) written in SystemVerilog and verified with [cocotb](https://www.cocotb.org/) on Icarus Verilog. It has full forwarding and load-use hazard detection and runs arbitrary RV32I programs without NOPs.

This is a self-education project to deepen my understanding of computer architecture
and digital design, from the RTL of a pipelined processor to its verification.

## Status

The pipeline is complete and runs real programs.

| Part | Modules | Status |
|---|---|---|
| IF  | `program_counter`, `imem`, `instruction_fetcher` (incl. IF/ID register) | done, tested |
| ID  | `instruction_decoder`, `immediate_generator`, `control_unit`, `register_file`, `decode_stage` | done, tested |
| EX  | `alu`, `branch_unit`, `execute_stage` | done, tested |
| MEM | `data_memory`, `memory_stage` | done, tested |
| WB  | `writeback_stage` | done, tested |
| Pipeline registers | `id_ex_reg`, `ex_mem_reg`, `mem_wb_reg` | done, tested |
| Hazards | `forwarding_unit`, `hazard_unit`, register file bypass | done, tested |
| Top level | `cpu_top` | done, 15 programs pass without NOPs |

| Situation | Cost |
|---|---|
| ALU result used by the next instruction | 0 cycles (forwarded) |
| Load result used by the next instruction | 1 stall cycle |
| Taken branch / jump | 2 cycles (no branch prediction yet) |

## Roadmap

1. **v0.1:** pass the official [riscv-tests](https://github.com/riscv-software-src/riscv-tests) for RV32I
2. Machine mode: Zicsr, exceptions, interrupts, performance counters
3. M extension with a multi-cycle divider
4. Branch prediction (BTB, bimodal, gshare, return address stack), measured with the performance counters
5. Instruction and data caches with prefetching
6. Out-of-order core, kept next to the in-order one as a baseline

## Repository layout

```
pipeRV/
├── doc/            documentation
├── rtl/            SystemVerilog sources, one module per file
└── sim/
    ├── helpers/    shared Python helpers: a small RV32I assembler, memory model
    ├── cpu_top/    programs run on the whole pipeline
    └── <module>/   one folder per module: Makefile + test_<module>.py
```

## Requirements

- Icarus Verilog 12 or newer (`-g2012`)
- Python 3.10+
- cocotb 2.x (`pip install cocotb`)

## Running the tests

Each module has its own test folder. To run one:

```bash
cd sim/register_file
make
```

To run all of them:

```bash
for t in sim/*/Makefile; do make -C "$(dirname "$t")" || break; done
```

Waveforms are written to `sim_build/` (`WAVES = 1` in every Makefile). `make clean` removes all build artifacts.

## Documentation

See [`doc/architecture.md`](doc/architecture.md) for the pipeline structure, module interfaces and design conventions.

## Acknowledgements

- Prof. Onur Mutlu's lectures on *Digital Design and Computer Architecture* (ETH Zürich),
  freely available on [YouTube](https://www.youtube.com/@OnurMutluLectures), were especially
  helpful throughout this project. Many thanks for making them public.