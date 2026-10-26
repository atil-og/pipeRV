module instruction_fetcher (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        stall,       // hold PC and IF/ID register
    input  logic        pc_sel,      // 1 = redirect to pc_target (taken branch / jump)
    input  logic [31:0] pc_target,
    output logic [31:0] instr_out,
    output logic [31:0] pc_out       // PC of instr_out, needed for branches, JAL and AUIPC
);

    localparam logic [31:0] NOP = 32'h00000013;  // addi x0, x0, 0

    logic [31:0] current_pc;
    logic [31:0] raw_instr;

    program_counter pc_inst (
        .clk       (clk),
        .rst_n     (rst_n),
        .stall     (stall),
        .pc_sel    (pc_sel),
        .pc_target (pc_target),
        .pc        (current_pc)
    );

    imem imem_inst (
        .read_address (current_pc),
        .instr        (raw_instr)
    );

    // IF/ID pipeline register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instr_out <= NOP;
            pc_out    <= 32'd0;
        end else if (pc_sel) begin
            // the instruction fetched this cycle is on the wrong path -> flush
            instr_out <= NOP;
            pc_out    <= 32'd0;
        end else if (!stall) begin
            instr_out <= raw_instr;
            pc_out    <= current_pc;
        end
    end

endmodule