import riscv_pkg::*;

import riscv_pkg::*;

module id_ex_reg (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        stall,      // hold contents
    input  logic        flush,      // insert a bubble (taken branch, load-use hazard)

    // control
    input  ex_ctrl_t    ex_ctrl_in,
    input  mem_ctrl_t   mem_ctrl_in,
    input  wb_ctrl_t    wb_ctrl_in,

    // data
    input  logic [31:0] pc_in,
    input  logic [31:0] rs1_data_in,
    input  logic [31:0] rs2_data_in,
    input  logic [31:0] imm_in,
    input  logic [4:0]  rs1_in,
    input  logic [4:0]  rs2_in,
    input  logic [4:0]  rd_in,
    input  logic [2:0]  funct3_in,

    output ex_ctrl_t    ex_ctrl_out,
    output mem_ctrl_t   mem_ctrl_out,
    output wb_ctrl_t    wb_ctrl_out,
    output logic [31:0] pc_out,
    output logic [31:0] rs1_data_out,
    output logic [31:0] rs2_data_out,
    output logic [31:0] imm_out,
    output logic [4:0]  rs1_out,
    output logic [4:0]  rs2_out,
    output logic [4:0]  rd_out,
    output logic [2:0]  funct3_out
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ex_ctrl_out  <= '0;
            mem_ctrl_out <= '0;
            wb_ctrl_out  <= '0;
            pc_out       <= '0;
            rs1_data_out <= '0;
            rs2_data_out <= '0;
            imm_out      <= '0;
            rs1_out      <= '0;
            rs2_out      <= '0;
            rd_out       <= '0;
            funct3_out   <= '0;
        end else if (flush) begin
            // Bubble: with all control signals at 0 the instruction
            // writes nothing and does not branch, the data does not matter.
            ex_ctrl_out  <= '0;
            mem_ctrl_out <= '0;
            wb_ctrl_out  <= '0;
        end else if (!stall) begin
            ex_ctrl_out  <= ex_ctrl_in;
            mem_ctrl_out <= mem_ctrl_in;
            wb_ctrl_out  <= wb_ctrl_in;
            pc_out       <= pc_in;
            rs1_data_out <= rs1_data_in;
            rs2_data_out <= rs2_data_in;
            imm_out      <= imm_in;
            rs1_out      <= rs1_in;
            rs2_out      <= rs2_in;
            rd_out       <= rd_in;
            funct3_out   <= funct3_in;
        end
    end

endmodule