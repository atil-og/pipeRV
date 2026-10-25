module imem(
    input logic [31 : 0] read_address,
    output logic [31 : 0] instr
    
);

reg [31 : 0] memory [0:1023];
// 31:2 is used in order to get the index of the address to read out of the program counter
// For example the address to be read is: 8 -> In the instructiom memory the index 2 has to be read, 
// therefore the program counter is always divided by four by cutting of the last two bits.
assign instr = memory[read_address[31:2]];

endmodule
