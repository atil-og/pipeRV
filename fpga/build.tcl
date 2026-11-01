# Build the pipeRV bitstream for the ZedBoard in Vivado non-project mode.
#
#   cd fpga && make                 (builds sw/blink first, then runs this script)
#   vivado -mode batch -source build.tcl
#
# Expects imem.mem and dmem.mem in fpga/build/. Results also go there:
#   pipeRV.bit, timing.rpt, utilization.rpt

set fpga  [file normalize [file dirname [info script]]]
set root  [file dirname $fpga]
set build $fpga/build
set part  xc7z020clg484-1

file mkdir $build
cd $build

foreach f {imem.mem dmem.mem} {
    if {![file exists $f]} { error "$build/$f is missing, build a program first (see fpga/Makefile)" }
}

# Sources: the package first, then every other module
read_verilog -sv $root/rtl/riscv_pkg.sv
foreach f [lsort [glob $root/rtl/*.sv]] {
    if {[file tail $f] ne "riscv_pkg.sv"} { read_verilog -sv $f }
}
read_verilog -sv $fpga/zedboard_top.sv
read_xdc $fpga/zedboard.xdc
read_mem [list $build/imem.mem $build/dmem.mem]

synth_design -top zedboard_top -part $part
opt_design
place_design
phys_opt_design
route_design

report_utilization    -file utilization.rpt
report_timing_summary -file timing.rpt

set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
puts "Worst negative slack: $wns ns"
if {$wns < 0} {
    puts "WARNING: timing not met, the design may not work reliably. See $build/timing.rpt"
}

write_bitstream -force pipeRV.bit
puts "Bitstream: $build/pipeRV.bit"