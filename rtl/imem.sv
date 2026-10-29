  module imem #(
      parameter int DEPTH = 1024                       // number of 32-bit words
  ) (
      input  logic [31:0] read_address,                // byte address
      output logic [31:0] instr
  );
      localparam int AW = $clog2(DEPTH);

      logic [31:0] memory [0:DEPTH-1];

      assign instr = memory[read_address[AW+1:2]];     // word index, upper bits ignored
  endmodule
