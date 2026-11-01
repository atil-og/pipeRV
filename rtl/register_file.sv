module register_file (
    input  logic        clk,
    input  logic [4:0]  addr_reg_1,
    input  logic [4:0]  addr_reg_2,
    input  logic [4:0]  write_destination,
    input  logic [31:0] write_data,
    input  logic        w_en,
    output logic [31:0] data_reg1,
    output logic [31:0] data_reg2
);

    logic [31:0] reg_file [0:31];

    // Internal bypass: if WB writes the register that ID reads in the same
    // cycle, return the new value instead of the one still in the array.
    assign data_reg1 = (addr_reg_1 == 5'd0)                          ? 32'd0      :
                       (w_en && write_destination == addr_reg_1)     ? write_data :
                                                                       reg_file[addr_reg_1];
    assign data_reg2 = (addr_reg_2 == 5'd0)                          ? 32'd0      :
                       (w_en && write_destination == addr_reg_2)     ? write_data :
                                                                       reg_file[addr_reg_2];

    always_ff @(posedge clk) begin
        if (w_en && (write_destination != 5'd0)) begin
            reg_file[write_destination] <= write_data;
        end
    end

endmodule