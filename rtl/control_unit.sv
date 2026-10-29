import riscv_pkg::*;

module control_unit (
    input  logic [6:0] opcode,
    input  logic [2:0] funct3,
    input  logic [6:0] funct7,
    output ex_ctrl_t   ex_ctrl,
    output mem_ctrl_t  mem_ctrl,
    output wb_ctrl_t   wb_ctrl
);

    // Opcodes
    localparam logic [6:0] OP_LUI    = 7'b0110111;
    localparam logic [6:0] OP_AUIPC  = 7'b0010111;
    localparam logic [6:0] OP_JAL    = 7'b1101111;
    localparam logic [6:0] OP_JALR   = 7'b1100111;
    localparam logic [6:0] OP_BRANCH = 7'b1100011;
    localparam logic [6:0] OP_LOAD   = 7'b0000011;
    localparam logic [6:0] OP_STORE  = 7'b0100011;
    localparam logic [6:0] OP_IMM    = 7'b0010011;
    localparam logic [6:0] OP_REG    = 7'b0110011;

    // ALU operation for R-type and I-type arithmetic, decoded from funct3/funct7
    function automatic logic [3:0] decode_alu_op(input logic [2:0] f3, input logic f7_bit5, input logic is_reg);
        case (f3)
            3'b000:  return (is_reg && f7_bit5) ? ALU_SUB : ALU_ADD;  // no subi
            3'b001:  return ALU_SLL;
            3'b010:  return ALU_SLT;
            3'b011:  return ALU_SLTU;
            3'b100:  return ALU_XOR;
            3'b101:  return f7_bit5 ? ALU_SRA : ALU_SRL;              // also for srai/srli
            3'b110:  return ALU_OR;
            default: return ALU_AND;                                  // 3'b111
        endcase
    endfunction

    always_comb begin
        // Defaults: everything off = NOP. Also prevents latches.
        ex_ctrl  = '0;
        mem_ctrl = '0;
        wb_ctrl  = '0;

        case (opcode)
            OP_REG: begin                       // add, sub, and, or, ...
                ex_ctrl.alu_op    = decode_alu_op(funct3, funct7[5], 1'b1);
                wb_ctrl.reg_write = 1'b1;
                wb_ctrl.wb_sel    = WB_ALU;
            end

            OP_IMM: begin                       // addi, andi, slli, ...
                ex_ctrl.alu_op    = decode_alu_op(funct3, funct7[5], 1'b0);
                ex_ctrl.alu_src_b = 1'b1;
                wb_ctrl.reg_write = 1'b1;
                wb_ctrl.wb_sel    = WB_ALU;
            end

            OP_LOAD: begin                      // lw, lh, lb, ...  addr = rs1 + imm
                ex_ctrl.alu_op     = ALU_ADD;
                ex_ctrl.alu_src_b  = 1'b1;
                mem_ctrl.mem_read  = 1'b1;
                wb_ctrl.reg_write  = 1'b1;
                wb_ctrl.wb_sel     = WB_MEM;
            end

            OP_STORE: begin                     // sw, sh, sb       addr = rs1 + imm
                ex_ctrl.alu_op     = ALU_ADD;
                ex_ctrl.alu_src_b  = 1'b1;
                mem_ctrl.mem_write = 1'b1;
            end

            OP_BRANCH: begin                    // beq, bne, blt, ... condition from funct3
                ex_ctrl.alu_op = ALU_SUB;
                ex_ctrl.branch = 1'b1;
            end

            OP_LUI: begin                       // rd = imm
                ex_ctrl.alu_op    = ALU_PASS_B;
                ex_ctrl.alu_src_b = 1'b1;
                wb_ctrl.reg_write = 1'b1;
                wb_ctrl.wb_sel    = WB_ALU;
            end

            OP_AUIPC: begin                     // rd = pc + imm
                ex_ctrl.alu_op    = ALU_ADD;
                ex_ctrl.alu_src_a = 1'b1;
                ex_ctrl.alu_src_b = 1'b1;
                wb_ctrl.reg_write = 1'b1;
                wb_ctrl.wb_sel    = WB_ALU;
            end

            OP_JAL: begin                       // rd = pc + 4, pc = pc + imm
                ex_ctrl.jump      = 1'b1;
                wb_ctrl.reg_write = 1'b1;
                wb_ctrl.wb_sel    = WB_PC4;
            end

            OP_JALR: begin                      // rd = pc + 4, pc = rs1 + imm
                ex_ctrl.alu_op    = ALU_ADD;
                ex_ctrl.alu_src_b = 1'b1;
                ex_ctrl.jalr      = 1'b1;
                wb_ctrl.reg_write = 1'b1;
                wb_ctrl.wb_sel    = WB_PC4;
            end

            default: ;                          // FENCE, ECALL, EBREAK, illegal -> NOP
        endcase
    end

endmodule