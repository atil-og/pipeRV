package riscv_pkg;

    // ALU operations
    localparam logic [3:0] ALU_ADD  = 4'd0;
    localparam logic [3:0] ALU_SUB  = 4'd1;
    localparam logic [3:0] ALU_SLL  = 4'd2;
    localparam logic [3:0] ALU_SLT  = 4'd3;
    localparam logic [3:0] ALU_SLTU = 4'd4;
    localparam logic [3:0] ALU_XOR  = 4'd5;
    localparam logic [3:0] ALU_SRL  = 4'd6;
    localparam logic [3:0] ALU_SRA  = 4'd7;
    localparam logic [3:0] ALU_OR   = 4'd8;
    localparam logic [3:0] ALU_AND  = 4'd9;
    localparam logic [3:0] ALU_PASS_B = 4'd10;  // for LUI: result = imm

    // Write-back source
    localparam logic [1:0] WB_ALU  = 2'd0;
    localparam logic [1:0] WB_MEM  = 2'd1;
    localparam logic [1:0] WB_PC4  = 2'd2;      // JAL / JALR: rd = pc + 4

    // Control signals used in the EX stage
    typedef struct packed {
        logic [3:0] alu_op;
        logic       alu_src_a;   // 0 = rs1, 1 = pc  (AUIPC)
        logic       alu_src_b;   // 0 = rs2, 1 = imm
        logic       branch;
        logic       jump;        // JAL
        logic       jalr;        // JALR: target = rs1 + imm
    } ex_ctrl_t;

    // Control signals used in the MEM stage
    typedef struct packed {
        logic       mem_read;
        logic       mem_write;
    } mem_ctrl_t;

    // Control signals used in the WB stage
    typedef struct packed {
        logic       reg_write;
        logic [1:0] wb_sel;
    } wb_ctrl_t;

endpackage