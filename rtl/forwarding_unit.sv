module forwarding_unit (
    // source registers of the instruction in EX
    input  logic [4:0] id_ex_rs1,
    input  logic [4:0] id_ex_rs2,

    // destination of the instruction one ahead (in MEM)
    input  logic       ex_mem_reg_write,
    input  logic [4:0] ex_mem_rd,

    // destination of the instruction two ahead (in WB)
    input  logic       mem_wb_reg_write,
    input  logic [4:0] mem_wb_rd,

    output logic [1:0] forward_a,       // 00 = register file, 01 = MEM/WB, 10 = EX/MEM
    output logic [1:0] forward_b
);

    localparam logic [1:0] FWD_NONE = 2'b00;
    localparam logic [1:0] FWD_WB   = 2'b01;
    localparam logic [1:0] FWD_MEM  = 2'b10;

    // EX/MEM wins over MEM/WB: if both write the same register, the instruction
    // in MEM is the newer one. x0 is never forwarded, it always reads as 0.
    //
    // Everything the function reads is passed as an argument. A function that
    // reads module signals directly is only re-evaluated when its arguments
    // change, so the output would miss changes of ex_mem_rd etc.
    function automatic logic [1:0] select(
        input logic [4:0] rs,
        input logic       em_write, input logic [4:0] em_rd,
        input logic       mw_write, input logic [4:0] mw_rd
    );
        if (em_write && em_rd != 5'd0 && em_rd == rs)
            return FWD_MEM;
        else if (mw_write && mw_rd != 5'd0 && mw_rd == rs)
            return FWD_WB;
        else
            return FWD_NONE;
    endfunction

    assign forward_a = select(id_ex_rs1, ex_mem_reg_write, ex_mem_rd, mem_wb_reg_write, mem_wb_rd);
    assign forward_b = select(id_ex_rs2, ex_mem_reg_write, ex_mem_rd, mem_wb_reg_write, mem_wb_rd);

endmodule