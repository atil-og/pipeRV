## pipeRV on the ZedBoard. Pins from Digilent's Zedboard-Master.xdc.

## 100 MHz oscillator (bank 13, 3.3 V)
set_property -dict {PACKAGE_PIN Y9 IOSTANDARD LVCMOS33} [get_ports GCLK]
create_clock -period 10.000 -name gclk [get_ports GCLK]

## LEDs LD0..LD7 (bank 33, 3.3 V)
set_property -dict {PACKAGE_PIN T22 IOSTANDARD LVCMOS33} [get_ports {LD[0]}]
set_property -dict {PACKAGE_PIN T21 IOSTANDARD LVCMOS33} [get_ports {LD[1]}]
set_property -dict {PACKAGE_PIN U22 IOSTANDARD LVCMOS33} [get_ports {LD[2]}]
set_property -dict {PACKAGE_PIN U21 IOSTANDARD LVCMOS33} [get_ports {LD[3]}]
set_property -dict {PACKAGE_PIN V22 IOSTANDARD LVCMOS33} [get_ports {LD[4]}]
set_property -dict {PACKAGE_PIN W22 IOSTANDARD LVCMOS33} [get_ports {LD[5]}]
set_property -dict {PACKAGE_PIN U19 IOSTANDARD LVCMOS33} [get_ports {LD[6]}]
set_property -dict {PACKAGE_PIN U14 IOSTANDARD LVCMOS33} [get_ports {LD[7]}]

## Centre button as reset (bank 34) and switches SW0..SW7 (banks 34/35).
## The voltage of these banks is set by jumper J18 (VADJ). Digilent's default
## is 1.8 V. If J18 is set to 2.5 V or 3.3 V, change LVCMOS18 accordingly.
set_property -dict {PACKAGE_PIN P16 IOSTANDARD LVCMOS18} [get_ports BTNC]
set_property -dict {PACKAGE_PIN F22 IOSTANDARD LVCMOS18} [get_ports {SW[0]}]
set_property -dict {PACKAGE_PIN G22 IOSTANDARD LVCMOS18} [get_ports {SW[1]}]
set_property -dict {PACKAGE_PIN H22 IOSTANDARD LVCMOS18} [get_ports {SW[2]}]
set_property -dict {PACKAGE_PIN F21 IOSTANDARD LVCMOS18} [get_ports {SW[3]}]
set_property -dict {PACKAGE_PIN H19 IOSTANDARD LVCMOS18} [get_ports {SW[4]}]
set_property -dict {PACKAGE_PIN H18 IOSTANDARD LVCMOS18} [get_ports {SW[5]}]
set_property -dict {PACKAGE_PIN H17 IOSTANDARD LVCMOS18} [get_ports {SW[6]}]
set_property -dict {PACKAGE_PIN M15 IOSTANDARD LVCMOS18} [get_ports {SW[7]}]

## Button and switches are asynchronous and synchronised in the design,
## the LEDs are slow outputs: no timing requirements on these ports.
set_false_path -from [get_ports BTNC]
set_false_path -from [get_ports {SW[*]}]
set_false_path -to   [get_ports {LD[*]}]
