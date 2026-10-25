module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/imem.fst");
    $dumpvars(0, imem);
end
endmodule
