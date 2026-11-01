# Load pipeRV.bit into the ZedBoard over JTAG (USB port J17 "PROG").
#
#   vivado -mode batch -source program.tcl

set bit [file normalize [file dirname [info script]]]/build/pipeRV.bit

open_hw_manager
connect_hw_server
open_hw_target

# The JTAG chain also contains the ARM debug port; pick the FPGA
set dev [lindex [get_hw_devices xc7z020*] 0]
current_hw_device $dev
refresh_hw_device $dev

set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev

close_hw_manager