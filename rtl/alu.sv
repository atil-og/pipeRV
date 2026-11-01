module alu
    import riscv_pkg::*;
(
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [3:0]  alu_op,
    output logic [31:0] result
);

    logic [4:0] shamt;
    assign shamt = b[4:0];  // RV32I only uses the lower 5 bits as shift amount

    always_comb begin
        case (alu_op)
            ALU_ADD:    result = a + b;
            ALU_SUB:    result = a - b;
            ALU_SLL:    result = a << shamt;
            ALU_SLT:    result = {31'd0, $signed(a) < $signed(b)};
            ALU_SLTU:   result = {31'd0, a < b};
            ALU_XOR:    result = a ^ b;
            ALU_SRL:    result = a >> shamt;
            ALU_SRA:    result = $unsigned($signed(a) >>> shamt);
            ALU_OR:     result = a | b;
            ALU_AND:    result = a & b;
            ALU_PASS_B: result = b;
            default:    result = 32'd0;
        endcase
    end

endmodule