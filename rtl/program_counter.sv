module program_counter(
    input logic clk,
    input logic rst_n,
    output reg [31 : 0] pc
);

always_ff @(posedge clk or negedge rst_n) begin
    if(!rst_n)
        pc <= 32'b0;
    else 
        pc <= pc + 4;
      
end
    
endmodule