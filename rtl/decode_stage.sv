import riscv_pkg::*;

module decode_stage (
    input  logic        clk,

    // from IF/ID
    input  logic [31:0] instr,

    // write-back port (comes back from the WB stage)
    input  logic        wb_reg_write,
    input  logic [4:0]  wb_rd,
    input  logic [31:0] wb_data,

    // to ID/EX
    output ex_ctrl_t    ex_ctrl,
    output mem_ctrl_t   mem_ctrl,
    output wb_ctrl_t    wb_ctrl,
    output logic [31:0] rs1_data,
    output logic [31:0] rs2_data,
    output logic [31:0] imm,
    output logic [4:0]  rs1,
    output logic [4:0]  rs2,
    output logic [4:0]  rd,
    output logic [2:0]  funct3
);

    logic [6:0] opcode;
    logic [6:0] funct7;

    instruction_decoder dec_inst (
        .instr      (instr),
        .opcode     (opcode),
        .rd         (rd),
        .addr_reg_1 (rs1),
        .addr_reg_2 (rs2),
        .funct3     (funct3),
        .funct7     (funct7),
        .imm        (imm)
    );

    control_unit ctrl_inst (
        .opcode   (opcode),
        .funct3   (funct3),
        .funct7   (funct7),
        .ex_ctrl  (ex_ctrl),
        .mem_ctrl (mem_ctrl),
        .wb_ctrl  (wb_ctrl)
    );

    register_file rf_inst (
        .clk               (clk),
        .addr_reg_1        (rs1),
        .addr_reg_2        (rs2),
        .write_destination (wb_rd),
        .write_data        (wb_data),
        .w_en              (wb_reg_write),
        .data_reg1         (rs1_data),
        .data_reg2         (rs2_data)
    );

endmodule