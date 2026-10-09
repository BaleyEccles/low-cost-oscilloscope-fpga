# ================================================================
# AD9484 DCO
#
# D4 = DCO+
# C4 = DCO-
# ================================================================

set_property PACKAGE_PIN D4 [get_ports clk_p]
set_property PACKAGE_PIN C4 [get_ports clk_n]

set_property IOSTANDARD LVDS_25 [get_ports {clk_p clk_n}]

# 100 MHz ADC DCO
set_property PERIOD 2.000 [get_nets adc_dco_ibuf]
create_clock -period 2.000 -name adc_dco [get_ports clk_p]


# ================================================================
# AD9484 DATA[0]
# ================================================================

set_property PACKAGE_PIN G5 [get_ports {data_p[0]}]
set_property PACKAGE_PIN G4 [get_ports {data_n[0]}]


# ================================================================
# AD9484 DATA[1]
# ================================================================

set_property PACKAGE_PIN G2 [get_ports {data_p[1]}]
set_property PACKAGE_PIN G1 [get_ports {data_n[1]}]


# ================================================================
# AD9484 DATA[2]
# ================================================================

set_property PACKAGE_PIN F4 [get_ports {data_p[2]}]
set_property PACKAGE_PIN F3 [get_ports {data_n[2]}]


# ================================================================
# AD9484 DATA[3]
# ================================================================

set_property PACKAGE_PIN F2 [get_ports {data_p[3]}]
set_property PACKAGE_PIN E1 [get_ports {data_n[3]}]


# ================================================================
# AD9484 DATA[4]
# ================================================================

set_property PACKAGE_PIN E2 [get_ports {data_p[4]}]
set_property PACKAGE_PIN D1 [get_ports {data_n[4]}]


# ================================================================
# AD9484 DATA[5]
# ================================================================

set_property PACKAGE_PIN F5 [get_ports {data_p[5]}]
set_property PACKAGE_PIN E5 [get_ports {data_n[5]}]


# ================================================================
# AD9484 DATA[6]
# ================================================================

set_property PACKAGE_PIN C1 [get_ports {data_p[6]}]
set_property PACKAGE_PIN B1 [get_ports {data_n[6]}]


# ================================================================
# AD9484 DATA[7]
# ================================================================

set_property PACKAGE_PIN E3 [get_ports {data_p[7]}]
set_property PACKAGE_PIN D3 [get_ports {data_n[7]}]


# All ADC data is LVDS
set_property IOSTANDARD LVDS_25 [get_ports {data_p[*] data_n[*]}]


# ================================================================
# UART
#
# FPGA T15 -> FT2232H Channel B BDBUS1 / RXD
# ================================================================

set_property PACKAGE_PIN T15 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

set_property DRIVE 8 [get_ports uart_tx]
set_property SLEW SLOW [get_ports uart_tx]n
