module branch_unit (
    input  logic [31:0] rs1,
    input  logic [31:0] rs2,
    input  logic [2:0]  funct3,
    output logic        taken
);

    always_comb begin
        case (funct3)
            3'b000:  taken = (rs1 == rs2);                     // beq
            3'b001:  taken = (rs1 != rs2);                     // bne
            3'b100:  taken = ($signed(rs1) <  $signed(rs2));   // blt
            3'b101:  taken = ($signed(rs1) >= $signed(rs2));   // bge
            3'b110:  taken = (rs1 <  rs2);                     // bltu
            3'b111:  taken = (rs1 >= rs2);                     // bgeu
            default: taken = 1'b0;                             // 010, 011 are not defined
        endcase
    end

endmodule