module program_counter (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        stall,       // hold the current PC (e.g. load-use hazard)
    input  logic        pc_sel,      // 0 = pc + 4, 1 = jump/branch target
    input  logic [31:0] pc_target,
    output logic [31:0] pc
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc <= 32'd0;
        else if (pc_sel)
            pc <= pc_target;
        else if (!stall)
            pc <= pc + 32'd4;
    end

endmodule