module memory_stage
    import riscv_pkg::*;
#(
    parameter int DEPTH = 1024
) (
    input  logic        clk,

    // from EX/MEM
    input  mem_ctrl_t   mem_ctrl,
    input  logic [31:0] addr,          // ALU result
    input  logic [31:0] store_data,
    input  logic [2:0]  funct3,        // access width and signedness

    // to MEM/WB
    output logic [31:0] load_data,     // sign- or zero-extended
    output logic        misaligned     // for a future exception, the access is still performed
);

    localparam logic [2:0] F3_B  = 3'b000;
    localparam logic [2:0] F3_H  = 3'b001;
    localparam logic [2:0] F3_W  = 3'b010;
    localparam logic [2:0] F3_BU = 3'b100;
    localparam logic [2:0] F3_HU = 3'b101;

    logic [1:0]  offset;
    logic [3:0]  be;
    logic [31:0] wdata;
    logic [31:0] rdata;
    logic [7:0]  rbyte;
    logic [15:0] rhalf;

    assign offset = addr[1:0];

    // ---------------------------------------------------------------
    // Store: place the data in the right byte lanes, enable only those
    // ---------------------------------------------------------------
    always_comb begin
        case (funct3[1:0])
            2'b00: begin                                   // sb
                wdata = {4{store_data[7:0]}};
                be    = 4'b0001 << offset;
            end
            2'b01: begin                                   // sh
                wdata = {2{store_data[15:0]}};
                be    = 4'b0011 << {offset[1], 1'b0};
            end
            default: begin                                 // sw
                wdata = store_data;
                be    = 4'b1111;
            end
        endcase
    end

    data_memory #(.DEPTH(DEPTH)) dmem_inst (
        .clk   (clk),
        .addr  (addr),
        .we    (mem_ctrl.mem_write),
        .be    (be),
        .wdata (wdata),
        .rdata (rdata)
    );

    // ---------------------------------------------------------------
    // Load: pick the byte / halfword lane and extend it
    // ---------------------------------------------------------------
    assign rbyte = rdata[8*offset    +: 8];
    assign rhalf = rdata[16*offset[1] +: 16];

    always_comb begin
        case (funct3)
            F3_B:    load_data = {{24{rbyte[7]}},  rbyte};
            F3_BU:   load_data = {24'd0,           rbyte};
            F3_H:    load_data = {{16{rhalf[15]}}, rhalf};
            F3_HU:   load_data = {16'd0,           rhalf};
            default: load_data = rdata;                     // lw
        endcase
    end

    // ---------------------------------------------------------------
    // Misalignment: halfword on an odd address, word not on a multiple of 4
    // ---------------------------------------------------------------
    always_comb begin
        misaligned = 1'b0;
        if (mem_ctrl.mem_read || mem_ctrl.mem_write) begin
            case (funct3[1:0])
                2'b01:   misaligned = offset[0];
                2'b10:   misaligned = (offset != 2'b00);
                default: misaligned = 1'b0;
            endcase
        end
    end

endmodule