module instruction_decoder (
        
    input  logic [31:0] instr,
    output logic [6:0]  opcode,
    output logic [4:0]  rd,
    output logic [4:0]  addr_reg_1,   // rs1
    output logic [4:0]  addr_reg_2,   // rs2
    output logic [2:0]  funct3,
    output logic [6:0]  funct7,
    output logic [31:0] imm

);


    assign opcode     = instr[6:0];
    assign rd         = instr[11:7];
    assign funct3     = instr[14:12];
    assign addr_reg_1 = instr[19:15];
    assign addr_reg_2 = instr[24:20];
    assign funct7     = instr[31:25];

immediate_generator imm_gen_inst(
    .instr(instr),
    .imm(imm)
);


endmodule