# pipeRV

A 5-stage pipelined RISC-V processor (RV32I) written in SystemVerilog and verified with [cocotb](https://www.cocotb.org/) on Icarus Verilog.

## Status

| Stage | Module | Status |
|---|---|---|
| IF  | `program_counter`, `imem`, `instruction_fetcher` (incl. IF/ID register) | done, tested |
| ID  | `instruction_decoder`, `immediate_generator`, `register_file` | done, tested |
| ID  | `control_unit`, `riscv_pkg` | in progress |
| ID/EX | `id_ex_reg` | in progress |
| EX  | ALU, branch unit | planned |
| MEM | data memory | planned |
| WB  | write-back mux | planned |
| —   | forwarding unit, hazard detection | planned |

## Repository layout

```
pipeRV/
├── doc/            documentation
├── rtl/            SystemVerilog sources, one module per file
└── tests/
    ├── helpers/    shared Python models used by several tests
    └── <module>/   one folder per module: Makefile + test_<module>.py
```

## Requirements

- Icarus Verilog 12 or newer (`-g2012`)
- Python 3.10+
- cocotb 2.x (`pip install cocotb`)

## Running the tests

Each module has its own test folder. To run one:

```bash
cd tests/register_file
make
```

To run all of them:

```bash
for t in tests/*/Makefile; do make -C "$(dirname "$t")" || break; done
```

Waveforms are written to `sim_build/` (`WAVES = 1` in every Makefile). `make clean` removes all build artifacts.

## Documentation

See [`doc/architecture.md`](doc/architecture.md) for the pipeline structure, module interfaces and design conventions.
