module hazard_unit (
    // instruction in EX
    input  logic       id_ex_mem_read,
    input  logic [4:0] id_ex_rd,

    // instruction in ID
    input  logic [4:0] id_rs1,
    input  logic [4:0] id_rs2,

    output logic       load_use_stall
);

    // A load in EX produces its value only at the end of MEM. The instruction
    // directly behind it would need that value at the start of EX, one cycle
    // too early for forwarding. So it waits one cycle in ID; after that, the
    // value comes from MEM/WB through the normal forwarding path.
    //
    // rs1/rs2 are compared even if the instruction in ID does not use them
    // (e.g. lui, jal, or rs2 of an I-type). That can cause an unnecessary
    // stall, which costs one cycle but never gives a wrong result.
    assign load_use_stall = id_ex_mem_read
                         && id_ex_rd != 5'd0
                         && (id_ex_rd == id_rs1 || id_ex_rd == id_rs2);

endmodule