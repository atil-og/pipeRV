module ex_mem_reg
    import riscv_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        stall,          // hold contents (e.g. later for a multi-cycle memory)

    input  mem_ctrl_t   mem_ctrl_in,
    input  wb_ctrl_t    wb_ctrl_in,
    input  logic [31:0] alu_result_in,
    input  logic [31:0] store_data_in,
    input  logic [31:0] pc_plus4_in,
    input  logic [4:0]  rd_in,
    input  logic [2:0]  funct3_in,

    output mem_ctrl_t   mem_ctrl_out,
    output wb_ctrl_t    wb_ctrl_out,
    output logic [31:0] alu_result_out,
    output logic [31:0] store_data_out,
    output logic [31:0] pc_plus4_out,
    output logic [4:0]  rd_out,
    output logic [2:0]  funct3_out
);

    // No flush input: a taken branch is resolved in EX and flushes only the
    // stages behind it. The branch itself moves on into MEM.

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem_ctrl_out   <= '0;
            wb_ctrl_out    <= '0;
            alu_result_out <= '0;
            store_data_out <= '0;
            pc_plus4_out   <= '0;
            rd_out         <= '0;
            funct3_out     <= '0;
        end else if (!stall) begin
            mem_ctrl_out   <= mem_ctrl_in;
            wb_ctrl_out    <= wb_ctrl_in;
            alu_result_out <= alu_result_in;
            store_data_out <= store_data_in;
            pc_plus4_out   <= pc_plus4_in;
            rd_out         <= rd_in;
            funct3_out     <= funct3_in;
        end
    end

endmodule