module writeback_stage
    import riscv_pkg::*;
(
    // from MEM/WB
    input  wb_ctrl_t    wb_ctrl,
    input  logic [31:0] alu_result,
    input  logic [31:0] load_data,
    input  logic [31:0] pc_plus4,
    input  logic [4:0]  rd,

    // to the register file write port (and later to the forwarding unit)
    output logic        reg_write,
    output logic [4:0]  wb_rd,
    output logic [31:0] wb_data
);

    always_comb begin
        case (wb_ctrl.wb_sel)
            WB_ALU:  wb_data = alu_result;
            WB_MEM:  wb_data = load_data;
            WB_PC4:  wb_data = pc_plus4;
            default: wb_data = 32'd0;          // 2'b11 is unused
        endcase
    end

    assign reg_write = wb_ctrl.reg_write;
    assign wb_rd     = rd;

endmodule