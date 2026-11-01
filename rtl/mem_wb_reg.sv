module mem_wb_reg
    import riscv_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    input  wb_ctrl_t    wb_ctrl_in,
    input  logic [31:0] alu_result_in,
    input  logic [31:0] load_data_in,
    input  logic [31:0] pc_plus4_in,
    input  logic [4:0]  rd_in,

    output wb_ctrl_t    wb_ctrl_out,
    output logic [31:0] alu_result_out,
    output logic [31:0] load_data_out,
    output logic [31:0] pc_plus4_out,
    output logic [4:0]  rd_out
);

    // No stall or flush: once an instruction has left MEM it always completes.
    // A multi-cycle memory later would need a bubble input here instead of a stall.

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wb_ctrl_out    <= '0;
            alu_result_out <= '0;
            load_data_out  <= '0;
            pc_plus4_out   <= '0;
            rd_out         <= '0;
        end else begin
            wb_ctrl_out    <= wb_ctrl_in;
            alu_result_out <= alu_result_in;
            load_data_out  <= load_data_in;
            pc_plus4_out   <= pc_plus4_in;
            rd_out         <= rd_in;
        end
    end

endmodule