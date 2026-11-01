module execute_stage
    import riscv_pkg::*;
(
    // from ID/EX
    input  ex_ctrl_t    ex_ctrl,
    input  logic [31:0] pc,
    input  logic [31:0] rs1_data,
    input  logic [31:0] rs2_data,
    input  logic [31:0] imm,
    input  logic [2:0]  funct3,

    // forwarding (driven by the forwarding unit, tie to 0 until it exists)
    input  logic [1:0]  forward_a,      // 00 = ID/EX, 01 = MEM/WB, 10 = EX/MEM
    input  logic [1:0]  forward_b,
    input  logic [31:0] ex_mem_result,  // ALU result of the instruction one ahead
    input  logic [31:0] wb_data,        // write-back value of the instruction two ahead

    // to EX/MEM
    output logic [31:0] alu_result,
    output logic [31:0] store_data,     // rs2 after forwarding, written by stores
    output logic [31:0] pc_plus4,       // rd value for JAL / JALR

    // to IF (and flush of IF/ID and ID/EX)
    output logic        pc_sel,
    output logic [31:0] pc_target
);

    localparam logic [1:0] FWD_NONE = 2'b00;
    localparam logic [1:0] FWD_WB   = 2'b01;
    localparam logic [1:0] FWD_MEM  = 2'b10;

    logic [31:0] rs1_fwd, rs2_fwd;
    logic [31:0] alu_a, alu_b;
    logic        branch_taken;

    // Forwarding muxes
    always_comb begin
        case (forward_a)
            FWD_MEM: rs1_fwd = ex_mem_result;
            FWD_WB:  rs1_fwd = wb_data;
            default: rs1_fwd = rs1_data;
        endcase
        case (forward_b)
            FWD_MEM: rs2_fwd = ex_mem_result;
            FWD_WB:  rs2_fwd = wb_data;
            default: rs2_fwd = rs2_data;
        endcase
    end

    // ALU operand muxes
    assign alu_a = ex_ctrl.alu_src_a ? pc  : rs1_fwd;
    assign alu_b = ex_ctrl.alu_src_b ? imm : rs2_fwd;

    alu alu_inst (
        .a      (alu_a),
        .b      (alu_b),
        .alu_op (ex_ctrl.alu_op),
        .result (alu_result)
    );

    branch_unit branch_inst (
        .rs1    (rs1_fwd),
        .rs2    (rs2_fwd),
        .funct3 (funct3),
        .taken  (branch_taken)
    );

    assign store_data = rs2_fwd;
    assign pc_plus4   = pc + 32'd4;

    // Branch / jump resolution
    assign pc_sel    = ex_ctrl.jump | ex_ctrl.jalr | (ex_ctrl.branch & branch_taken);
    assign pc_target = ex_ctrl.jalr ? {alu_result[31:1], 1'b0}   // (rs1 + imm) & ~1
                                    : pc + imm;                  // branch, JAL

endmodule