// Memory-mapped I/O. Every address with bit 31 set belongs to I/O instead of
// the data memory.
//
//   0x8000_0000  LEDS      read/write  bits [7:0] drive the LEDs
//   0x8000_0004  SWITCHES  read only   bits [7:0] are the switches
//
// Use lw/sw: the registers ignore the access width.

module mmio
    import riscv_pkg::*;
(
    input  logic        clk,
    input  logic        rst_n,

    // access in the MEM stage (from EX/MEM)
    input  mem_ctrl_t   mem_ctrl,
    input  logic [31:0] addr,
    input  logic [31:0] store_data,

    output logic        is_io,          // the data memory must ignore this access
    output logic [31:0] io_rdata,

    // board
    input  logic [7:0]  switches,       // already synchronised to clk
    output logic [7:0]  leds
);

    localparam logic [1:0] REG_LEDS     = 2'd0;
    localparam logic [1:0] REG_SWITCHES = 2'd1;

    logic [1:0] reg_sel;

    assign is_io   = addr[31];
    assign reg_sel = addr[3:2];

    always_comb begin
        case (reg_sel)
            REG_LEDS:     io_rdata = {24'd0, leds};
            REG_SWITCHES: io_rdata = {24'd0, switches};
            default:      io_rdata = 32'd0;
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            leds <= 8'd0;
        else if (mem_ctrl.mem_write && is_io && reg_sel == REG_LEDS)
            leds <= store_data[7:0];
    end

endmodule