module cpu_top
    import riscv_pkg::*;
(
    input  logic clk,
    input  logic rst_n
);

    // =======================================================================
    // Signals, named after the pipeline register or stage they come from
    // =======================================================================

    // IF/ID
    logic [31:0] if_id_instr, if_id_pc;

    // ID (combinational outputs of the decode stage)
    ex_ctrl_t    id_ex_ctrl;
    mem_ctrl_t   id_mem_ctrl;
    wb_ctrl_t    id_wb_ctrl;
    logic [31:0] id_rs1_data, id_rs2_data, id_imm;
    logic [4:0]  id_rs1, id_rs2, id_rd;
    logic [2:0]  id_funct3;

    // ID/EX
    ex_ctrl_t    id_ex_ex_ctrl;
    mem_ctrl_t   id_ex_mem_ctrl;
    wb_ctrl_t    id_ex_wb_ctrl;
    logic [31:0] id_ex_pc, id_ex_rs1_data, id_ex_rs2_data, id_ex_imm;
    logic [4:0]  id_ex_rs1, id_ex_rs2, id_ex_rd;
    logic [2:0]  id_ex_funct3;

    // EX (combinational outputs of the execute stage)
    logic [31:0] ex_alu_result, ex_store_data, ex_pc_plus4;
    logic        ex_pc_sel;
    logic [31:0] ex_pc_target;

    // EX/MEM
    mem_ctrl_t   ex_mem_mem_ctrl;
    wb_ctrl_t    ex_mem_wb_ctrl;
    logic [31:0] ex_mem_alu_result, ex_mem_store_data, ex_mem_pc_plus4;
    logic [4:0]  ex_mem_rd;
    logic [2:0]  ex_mem_funct3;

    // MEM
    logic [31:0] mem_load_data;
    logic        mem_misaligned;     // not used yet, becomes an exception later

    // MEM/WB
    wb_ctrl_t    mem_wb_wb_ctrl;
    logic [31:0] mem_wb_alu_result, mem_wb_load_data, mem_wb_pc_plus4;
    logic [4:0]  mem_wb_rd;

    // WB
    logic        wb_reg_write;
    logic [4:0]  wb_rd;
    logic [31:0] wb_data;

    // Hazard handling
    logic        stall;                // load-use hazard: hold PC and IF/ID, bubble into ID/EX
    logic [1:0]  forward_a, forward_b;
    logic [31:0] ex_mem_fwd_value;     // value the instruction in MEM will write back

    hazard_unit hazard_inst (
        .id_ex_mem_read (id_ex_mem_ctrl.mem_read),
        .id_ex_rd       (id_ex_rd),
        .id_rs1         (id_rs1),
        .id_rs2         (id_rs2),
        .load_use_stall (stall)
    );

    // =======================================================================
    // IF (+ IF/ID register)
    // =======================================================================

    instruction_fetcher fetch_inst (
        .clk       (clk),
        .rst_n     (rst_n),
        .stall     (stall),
        .pc_sel    (ex_pc_sel),       // also flushes IF/ID
        .pc_target (ex_pc_target),
        .instr_out (if_id_instr),
        .pc_out    (if_id_pc)
    );

    // =======================================================================
    // ID
    // =======================================================================

    decode_stage decode_inst (
        .clk          (clk),
        .instr        (if_id_instr),
        .wb_reg_write (wb_reg_write),
        .wb_rd        (wb_rd),
        .wb_data      (wb_data),
        .ex_ctrl      (id_ex_ctrl),
        .mem_ctrl     (id_mem_ctrl),
        .wb_ctrl      (id_wb_ctrl),
        .rs1_data     (id_rs1_data),
        .rs2_data     (id_rs2_data),
        .imm          (id_imm),
        .rs1          (id_rs1),
        .rs2          (id_rs2),
        .rd           (id_rd),
        .funct3       (id_funct3)
    );

    id_ex_reg id_ex_inst (
        .clk          (clk),
        .rst_n        (rst_n),
        .stall        (1'b0),
        .flush        (ex_pc_sel | stall),   // wrong path, or bubble while ID waits for a load
        .ex_ctrl_in   (id_ex_ctrl),
        .mem_ctrl_in  (id_mem_ctrl),
        .wb_ctrl_in   (id_wb_ctrl),
        .pc_in        (if_id_pc),
        .rs1_data_in  (id_rs1_data),
        .rs2_data_in  (id_rs2_data),
        .imm_in       (id_imm),
        .rs1_in       (id_rs1),
        .rs2_in       (id_rs2),
        .rd_in        (id_rd),
        .funct3_in    (id_funct3),
        .ex_ctrl_out  (id_ex_ex_ctrl),
        .mem_ctrl_out (id_ex_mem_ctrl),
        .wb_ctrl_out  (id_ex_wb_ctrl),
        .pc_out       (id_ex_pc),
        .rs1_data_out (id_ex_rs1_data),
        .rs2_data_out (id_ex_rs2_data),
        .imm_out      (id_ex_imm),
        .rs1_out      (id_ex_rs1),
        .rs2_out      (id_ex_rs2),
        .rd_out       (id_ex_rd),
        .funct3_out   (id_ex_funct3)
    );

    // =======================================================================
    // EX
    // =======================================================================

    forwarding_unit forwarding_inst (
        .id_ex_rs1        (id_ex_rs1),
        .id_ex_rs2        (id_ex_rs2),
        .ex_mem_reg_write (ex_mem_wb_ctrl.reg_write),
        .ex_mem_rd        (ex_mem_rd),
        .mem_wb_reg_write (mem_wb_wb_ctrl.reg_write),
        .mem_wb_rd        (mem_wb_rd),
        .forward_a        (forward_a),
        .forward_b        (forward_b)
    );

    // For JAL/JALR the result is pc + 4, not the ALU output. For a load the
    // value does not exist yet in MEM; the hazard unit stalls that case.
    assign ex_mem_fwd_value = (ex_mem_wb_ctrl.wb_sel == WB_PC4) ? ex_mem_pc_plus4
                                                                : ex_mem_alu_result;

    execute_stage execute_inst (
        .ex_ctrl       (id_ex_ex_ctrl),
        .pc            (id_ex_pc),
        .rs1_data      (id_ex_rs1_data),
        .rs2_data      (id_ex_rs2_data),
        .imm           (id_ex_imm),
        .funct3        (id_ex_funct3),
        .forward_a     (forward_a),
        .forward_b     (forward_b),
        .ex_mem_result (ex_mem_fwd_value),
        .wb_data       (wb_data),
        .alu_result    (ex_alu_result),
        .store_data    (ex_store_data),
        .pc_plus4      (ex_pc_plus4),
        .pc_sel        (ex_pc_sel),
        .pc_target     (ex_pc_target)
    );

    ex_mem_reg ex_mem_inst (
        .clk            (clk),
        .rst_n          (rst_n),
        .stall          (1'b0),
        .mem_ctrl_in    (id_ex_mem_ctrl),
        .wb_ctrl_in     (id_ex_wb_ctrl),
        .alu_result_in  (ex_alu_result),
        .store_data_in  (ex_store_data),
        .pc_plus4_in    (ex_pc_plus4),
        .rd_in          (id_ex_rd),
        .funct3_in      (id_ex_funct3),
        .mem_ctrl_out   (ex_mem_mem_ctrl),
        .wb_ctrl_out    (ex_mem_wb_ctrl),
        .alu_result_out (ex_mem_alu_result),
        .store_data_out (ex_mem_store_data),
        .pc_plus4_out   (ex_mem_pc_plus4),
        .rd_out         (ex_mem_rd),
        .funct3_out     (ex_mem_funct3)
    );

    // =======================================================================
    // MEM
    // =======================================================================

    memory_stage memory_inst (
        .clk        (clk),
        .mem_ctrl   (ex_mem_mem_ctrl),
        .addr       (ex_mem_alu_result),
        .store_data (ex_mem_store_data),
        .funct3     (ex_mem_funct3),
        .load_data  (mem_load_data),
        .misaligned (mem_misaligned)
    );

    mem_wb_reg mem_wb_inst (
        .clk            (clk),
        .rst_n          (rst_n),
        .wb_ctrl_in     (ex_mem_wb_ctrl),
        .alu_result_in  (ex_mem_alu_result),
        .load_data_in   (mem_load_data),
        .pc_plus4_in    (ex_mem_pc_plus4),
        .rd_in          (ex_mem_rd),
        .wb_ctrl_out    (mem_wb_wb_ctrl),
        .alu_result_out (mem_wb_alu_result),
        .load_data_out  (mem_wb_load_data),
        .pc_plus4_out   (mem_wb_pc_plus4),
        .rd_out         (mem_wb_rd)
    );

    // =======================================================================
    // WB
    // =======================================================================

    writeback_stage writeback_inst (
        .wb_ctrl    (mem_wb_wb_ctrl),
        .alu_result (mem_wb_alu_result),
        .load_data  (mem_wb_load_data),
        .pc_plus4   (mem_wb_pc_plus4),
        .rd         (mem_wb_rd),
        .reg_write  (wb_reg_write),
        .wb_rd      (wb_rd),
        .wb_data    (wb_data)
    );

endmodule