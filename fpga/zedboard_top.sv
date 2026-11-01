// pipeRV on the ZedBoard (Zynq-7020). Uses only the programmable logic; the
// ARM cores are not involved.
//
//   GCLK  100 MHz oscillator -> MMCM -> 50 MHz CPU clock
//   BTNC  reset (held while pressed)
//   SW    switches, readable at 0x8000_0004
//   LD    LEDs, written at 0x8000_0000
//
// The program is loaded into the memories at configuration time from
// imem.mem / dmem.mem (built from sw/ by fpga/Makefile).

module zedboard_top #(
    parameter IMEM_INIT = "imem.mem",
    parameter DMEM_INIT = "dmem.mem"
) (
    input  logic       GCLK,
    input  logic       BTNC,
    input  logic [7:0] SW,
    output logic [7:0] LD
);

    // -----------------------------------------------------------------------
    // Clock: 100 MHz in, 50 MHz out (VCO = 100 MHz * 10 = 1000 MHz, / 20)
    // For 100 MHz set CLKOUT0_DIVIDE_F to 10.0, but check the timing report.
    // -----------------------------------------------------------------------
    logic clk, clk_mmcm, clkfb_out, clkfb_in, locked;

    MMCME2_BASE #(
        .CLKIN1_PERIOD    (10.0),
        .DIVCLK_DIVIDE    (1),
        .CLKFBOUT_MULT_F  (10.0),
        .CLKOUT0_DIVIDE_F (20.0)
    ) mmcm_inst (
        .CLKIN1   (GCLK),
        .CLKFBIN  (clkfb_in),
        .CLKFBOUT (clkfb_out),
        .CLKOUT0  (clk_mmcm),
        .LOCKED   (locked),
        .PWRDWN   (1'b0),
        .RST      (1'b0),
        .CLKFBOUTB(), .CLKOUT0B(), .CLKOUT1(), .CLKOUT1B(), .CLKOUT2(),
        .CLKOUT2B(), .CLKOUT3(), .CLKOUT3B(), .CLKOUT4(), .CLKOUT5(), .CLKOUT6()
    );

    BUFG clkfb_buf (.I(clkfb_out), .O(clkfb_in));
    BUFG clk_buf   (.I(clk_mmcm),  .O(clk));

    // -----------------------------------------------------------------------
    // Reset: asserted asynchronously (button or MMCM not locked yet),
    // released synchronously to clk. The initial value makes the design come
    // up in reset right after configuration.
    // -----------------------------------------------------------------------
    logic       rst_req;
    logic [3:0] rst_sync = 4'b0000;
    logic       rst_n;

    assign rst_req = BTNC | ~locked;

    always_ff @(posedge clk or posedge rst_req) begin
        if (rst_req) rst_sync <= 4'b0000;
        else         rst_sync <= {rst_sync[2:0], 1'b1};
    end

    assign rst_n = rst_sync[3];

    // -----------------------------------------------------------------------
    // Switches: two flip-flops against metastability
    // -----------------------------------------------------------------------
    logic [7:0] sw_meta, sw_sync;

    always_ff @(posedge clk) begin
        sw_meta <= SW;
        sw_sync <= sw_meta;
    end

    // -----------------------------------------------------------------------
    // CPU
    // -----------------------------------------------------------------------
    cpu_top #(
        .IMEM_INIT (IMEM_INIT),
        .DMEM_INIT (DMEM_INIT)
    ) cpu_inst (
        .clk      (clk),
        .rst_n    (rst_n),
        .switches (sw_sync),
        .leds     (LD)
    );

endmodule