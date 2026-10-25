module register_file(
    input logic clk,
    input logic [0 : 4] addr_reg_1,
    input logic [0 : 4] addr_reg_2,
    input logic [0 : 4] write_destination,
    input logic [31 : 0] write_data,
    input logic w_en,
    output logic [31 : 0] data_reg1,
    output logic [31 : 0] data_reg2
)

reg [0:31] reg_file [31:0];

assign data_reg1 = (addr_reg_1 == 5'b0) ? 32'b0 : reg_file[addr_reg_1];
assign data_reg2 = (addr_reg_2 == 5'b0) ? 32'b0 : reg_file[addr_reg_2];

always_ff @(posedge clk) begin
    if (w_en && (write_destination != 5'b0)) begin
        reg_file[write_destination] <= write_data;
    end
end

endmodule

