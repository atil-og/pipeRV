module data_memory #(
    parameter int    DEPTH     = 1024,            // number of 32-bit words
    parameter        INIT_FILE = ""             // hex file, one 32-bit word per line
) (
    input  logic        clk,
    input  logic [31:0] addr,                     // byte address, lower 2 bits ignored
    input  logic        we,
    input  logic [3:0]  be,                       // byte enables, be[i] writes wdata[8*i +: 8]
    input  logic [31:0] wdata,
    output logic [31:0] rdata                     // whole word, read combinationally
);

    localparam int AW = $clog2(DEPTH);

    logic [31:0] memory [0:DEPTH-1];
    logic [AW-1:0] index;

    initial begin
        if (INIT_FILE != "") $readmemh(INIT_FILE, memory);
    end

    assign index = addr[AW+1:2];                  // upper address bits are ignored (wrap-around)
    assign rdata = memory[index];

    always_ff @(posedge clk) begin
        if (we) begin
            for (int i = 0; i < 4; i++) begin
                if (be[i]) memory[index][8*i +: 8] <= wdata[8*i +: 8];
            end
        end
    end

endmodule