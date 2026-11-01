module imem #(
    parameter int    DEPTH     = 1024,               // number of 32-bit words
    parameter        INIT_FILE = ""                // hex file, one 32-bit word per line
) (
    input  logic [31:0] read_address,                // byte address
    output logic [31:0] instr
);
    localparam int AW = $clog2(DEPTH);

    logic [31:0] memory [0:DEPTH-1];

    // On the FPGA the program is part of the bitstream. In simulation the
    // testbenches write the array directly and leave INIT_FILE empty.
    initial begin
        if (INIT_FILE != "") $readmemh(INIT_FILE, memory);
    end

    assign instr = memory[read_address[AW+1:2]];     // word index, upper bits ignored
endmodule