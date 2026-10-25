module instruction_fetch(
    input logic clk,
    input logic rst_n,
    output logic [31:0] instr_out
);

logic [31:0] current_pc;
logic [31:0] raw_instr;

program_counter pc_inst (
    .clk(clk),
    .rst_n(rst_n),
    .pc(current_pc)
);

imem imem_inst(
    .read_address(current_pc),
    .instr(raw_instr)
);

always_ff @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
        instr_out <= 32'h00000013;
    end else begin
        instr_out <= raw_instr;
    end
end


endmodule