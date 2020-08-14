EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A3 16535 11693
encoding utf-8
Sheet 1 1
Title "Raspberry Pi HAT"
Date ""
Rev "A"
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Mechanical:MountingHole H1
U 1 1 5834BC4A
P 4600 7800
F 0 "H1" H 4450 7900 60  0000 C CNN
F 1 "3mm_Mounting_Hole" H 4600 7650 60  0000 C CNN
F 2 "project_footprints:NPTH_3mm_ID" H 4500 7800 60  0001 C CNN
F 3 "" H 4500 7800 60  0001 C CNN
	1    4600 7800
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5834BCDF
P 5600 7800
F 0 "H2" H 5450 7900 60  0000 C CNN
F 1 "3mm_Mounting_Hole" H 5600 7650 60  0000 C CNN
F 2 "project_footprints:NPTH_3mm_ID" H 5500 7800 60  0001 C CNN
F 3 "" H 5500 7800 60  0001 C CNN
	1    5600 7800
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H3
U 1 1 5834BD62
P 4600 8350
F 0 "H3" H 4450 8450 60  0000 C CNN
F 1 "3mm_Mounting_Hole" H 4600 8200 60  0000 C CNN
F 2 "project_footprints:NPTH_3mm_ID" H 4500 8350 60  0001 C CNN
F 3 "" H 4500 8350 60  0001 C CNN
	1    4600 8350
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5834BDED
P 5650 8350
F 0 "H4" H 5500 8450 60  0000 C CNN
F 1 "3mm_Mounting_Hole" H 5650 8200 60  0000 C CNN
F 2 "project_footprints:NPTH_3mm_ID" H 5550 8350 60  0001 C CNN
F 3 "" H 5550 8350 60  0001 C CNN
	1    5650 8350
	1    0    0    -1  
$EndComp
$Comp
L actuators-rev2-rescue:OX40HAT-raspberrypi_hat J5
U 1 1 58DFC771
P 2600 2250
F 0 "J5" H 2950 2350 50  0000 C CNN
F 1 "40HAT" H 2300 2350 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 2600 2450 50  0001 C CNN
F 3 "" H 1900 2250 50  0000 C CNN
	1    2600 2250
	1    0    0    -1  
$EndComp
Text Notes 4400 7550 0    118  ~ 24
Mounting Holes
Text Notes 1300 2000 0    118  ~ 24
40-Pin HAT Connector
Wire Wire Line
	2000 4150 1600 4150
Wire Wire Line
	3200 2850 3600 2850
Wire Wire Line
	3200 3150 3600 3150
Wire Wire Line
	3200 3650 3600 3650
Wire Wire Line
	3200 2450 3600 2450
Text Notes 850  1250 0    100  ~ 0
This is based on the official Raspberry Pi spec to be able to call an extension board a HAT.\nhttps://github.com/raspberrypi/hats/blob/master/designguide.md
$Comp
L Transistor_Array:ULN2003A U1
U 1 1 5EBC03CF
P 5750 2850
F 0 "U1" H 5750 3517 50  0000 C CNN
F 1 "ULN2003A" H 5750 3426 50  0000 C CNN
F 2 "Package_DIP:DIP-16_W7.62mm" H 5800 2300 50  0001 L CNN
F 3 "http://www.ti.com/lit/ds/symlink/uln2003a.pdf" H 5850 2650 50  0001 C CNN
	1    5750 2850
	1    0    0    -1  
$EndComp
Wire Wire Line
	5350 2650 5250 2650
Wire Wire Line
	5250 2650 5250 2750
Wire Wire Line
	5350 2850 5250 2850
Wire Wire Line
	5250 2850 5250 2950
Wire Wire Line
	5250 2950 5350 2950
Wire Wire Line
	5250 2750 5350 2750
Wire Wire Line
	5350 3050 5250 3050
Wire Wire Line
	5250 3050 5250 3150
Wire Wire Line
	5250 3250 5350 3250
Wire Wire Line
	5350 3150 5250 3150
Connection ~ 5250 3150
Wire Wire Line
	5250 3150 5250 3250
Wire Wire Line
	6150 2650 6300 2650
Wire Wire Line
	6300 2650 6300 2750
Wire Wire Line
	6300 2750 6150 2750
Wire Wire Line
	6150 2850 6300 2850
Wire Wire Line
	6300 2850 6300 2950
Wire Wire Line
	6300 2950 6150 2950
Wire Wire Line
	6150 3050 6300 3050
Wire Wire Line
	6300 3050 6300 3150
Wire Wire Line
	6300 3150 6150 3150
Wire Wire Line
	6300 3150 6300 3250
Wire Wire Line
	6300 3250 6150 3250
Connection ~ 6300 3150
Text Label 5750 3450 0    50   ~ 0
GND
$Comp
L Connector:Screw_Terminal_01x02 J3
U 1 1 5EBC6173
P 7200 3150
F 0 "J3" H 7280 3142 50  0000 L CNN
F 1 "Screw_Terminal_01x02" H 7280 3051 50  0000 L CNN
F 2 "TerminalBlock:TerminalBlock_Altech_AK300-2_P5.00mm" H 7200 3150 50  0001 C CNN
F 3 "~" H 7200 3150 50  0001 C CNN
	1    7200 3150
	1    0    0    -1  
$EndComp
Connection ~ 6300 2850
Wire Wire Line
	6150 2450 6500 2450
Wire Wire Line
	6850 2950 7000 2950
Wire Wire Line
	6850 3250 7000 3250
$Comp
L power:GND #PWR0102
U 1 1 5EBE4CA9
P 5750 3450
F 0 "#PWR0102" H 5750 3200 50  0001 C CNN
F 1 "GND" H 5755 3277 50  0000 C CNN
F 2 "" H 5750 3450 50  0001 C CNN
F 3 "" H 5750 3450 50  0001 C CNN
	1    5750 3450
	1    0    0    -1  
$EndComp
$Comp
L power:+24V #PWR0105
U 1 1 5EBED3E5
P 6850 1850
F 0 "#PWR0105" H 6850 1700 50  0001 C CNN
F 1 "+24V" H 6865 2023 50  0000 C CNN
F 2 "" H 6850 1850 50  0001 C CNN
F 3 "" H 6850 1850 50  0001 C CNN
	1    6850 1850
	1    0    0    -1  
$EndComp
Connection ~ 6850 2050
$Comp
L power:+5V #PWR0107
U 1 1 5EBC64E1
P 3350 2200
F 0 "#PWR0107" H 3350 2050 50  0001 C CNN
F 1 "+5V" H 3365 2373 50  0000 C CNN
F 2 "" H 3350 2200 50  0001 C CNN
F 3 "" H 3350 2200 50  0001 C CNN
	1    3350 2200
	1    0    0    -1  
$EndComp
Wire Wire Line
	3200 2250 3350 2250
Wire Wire Line
	3350 2250 3350 2200
Wire Wire Line
	3200 2350 3350 2350
Wire Wire Line
	3350 2350 3350 2250
Connection ~ 3350 2250
Wire Wire Line
	1600 2650 1600 3450
Wire Wire Line
	1600 3450 2000 3450
Wire Wire Line
	1600 3450 1600 4150
Connection ~ 1600 3450
$Comp
L power:GND #PWR0109
U 1 1 5EBD2A73
P 1600 4350
F 0 "#PWR0109" H 1600 4100 50  0001 C CNN
F 1 "GND" H 1605 4177 50  0000 C CNN
F 2 "" H 1600 4350 50  0001 C CNN
F 3 "" H 1600 4350 50  0001 C CNN
	1    1600 4350
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0110
U 1 1 5EBD3294
P 3600 4350
F 0 "#PWR0110" H 3600 4100 50  0001 C CNN
F 1 "GND" H 3605 4177 50  0000 C CNN
F 2 "" H 3600 4350 50  0001 C CNN
F 3 "" H 3600 4350 50  0001 C CNN
	1    3600 4350
	1    0    0    -1  
$EndComp
Wire Wire Line
	3600 4350 3600 3850
Wire Wire Line
	3200 3850 3600 3850
Connection ~ 3600 3850
Wire Wire Line
	3600 3850 3600 3650
Wire Wire Line
	3600 3150 3600 3650
Connection ~ 3600 3150
Connection ~ 3600 3650
Wire Wire Line
	3600 3150 3600 2850
Connection ~ 3600 2850
Wire Wire Line
	3600 2850 3600 2450
Wire Wire Line
	1600 4150 1600 4350
Connection ~ 1600 4150
Wire Wire Line
	6500 2450 6500 2050
Wire Wire Line
	6500 2050 6850 2050
Wire Wire Line
	6850 2950 6850 3250
Wire Wire Line
	6850 2050 6850 1850
Text GLabel 3250 3750 2    50   Input ~ 0
BCM12
Wire Wire Line
	3200 3750 3250 3750
Text GLabel 4500 3150 0    50   Input ~ 0
BCM12
Text GLabel 4500 2850 0    50   Input ~ 0
BCM17
Wire Wire Line
	1600 2650 2000 2650
Text GLabel 1950 2750 0    50   Input ~ 0
BCM17
Text GLabel 1950 2850 0    50   Input ~ 0
BCM27
Wire Wire Line
	2000 2750 1950 2750
Wire Wire Line
	1950 2850 2000 2850
$Comp
L power:GND #PWR0111
U 1 1 5EBE3807
P 3450 6000
F 0 "#PWR0111" H 3450 5750 50  0001 C CNN
F 1 "GND" H 3455 5827 50  0000 C CNN
F 2 "" H 3450 6000 50  0001 C CNN
F 3 "" H 3450 6000 50  0001 C CNN
	1    3450 6000
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR0104
U 1 1 5EBEAA9A
P 3450 5100
F 0 "#PWR0104" H 3450 4950 50  0001 C CNN
F 1 "+5V" H 3465 5273 50  0000 C CNN
F 2 "" H 3450 5100 50  0001 C CNN
F 3 "" H 3450 5100 50  0001 C CNN
	1    3450 5100
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0103
U 1 1 5EBE95B2
P 1750 6000
F 0 "#PWR0103" H 1750 5750 50  0001 C CNN
F 1 "GND" H 1755 5827 50  0000 C CNN
F 2 "" H 1750 6000 50  0001 C CNN
F 3 "" H 1750 6000 50  0001 C CNN
	1    1750 6000
	1    0    0    -1  
$EndComp
Wire Wire Line
	1750 5900 1900 5900
Wire Wire Line
	1750 6000 1750 5900
$Comp
L Connector:Screw_Terminal_01x02 J7
U 1 1 5ED9A118
P 7200 2050
F 0 "J7" H 7280 2042 50  0000 L CNN
F 1 "Screw_Terminal_01x02" H 7280 1951 50  0000 L CNN
F 2 "TerminalBlock:TerminalBlock_Altech_AK300-2_P5.00mm" H 7200 2050 50  0001 C CNN
F 3 "~" H 7200 2050 50  0001 C CNN
	1    7200 2050
	1    0    0    -1  
$EndComp
Wire Wire Line
	6850 2050 7000 2050
Wire Wire Line
	7000 2150 7000 2300
$Comp
L power:GND #PWR01
U 1 1 5EDA0DD0
P 7000 2300
F 0 "#PWR01" H 7000 2050 50  0001 C CNN
F 1 "GND" H 7005 2127 50  0000 C CNN
F 2 "" H 7000 2300 50  0001 C CNN
F 3 "" H 7000 2300 50  0001 C CNN
	1    7000 2300
	1    0    0    -1  
$EndComp
Wire Wire Line
	3450 5100 3450 5500
$Comp
L Device:CP1 C1
U 1 1 5EC29A26
P 3450 5850
F 0 "C1" H 3565 5896 50  0000 L CNN
F 1 "CP1" H 3565 5805 50  0000 L CNN
F 2 "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm" H 3450 5850 50  0001 C CNN
F 3 "~" H 3450 5850 50  0001 C CNN
	1    3450 5850
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x02 J6
U 1 1 5EDB7C68
P 3650 5500
F 0 "J6" H 3730 5492 50  0000 L CNN
F 1 "Conn_01x02" H 3730 5401 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 3650 5500 50  0001 C CNN
F 3 "~" H 3650 5500 50  0001 C CNN
	1    3650 5500
	1    0    0    -1  
$EndComp
Wire Wire Line
	3300 5800 3300 5600
Wire Wire Line
	3300 5600 3450 5600
Wire Wire Line
	3450 5700 3450 5600
Connection ~ 3450 5600
Wire Wire Line
	3300 5900 3300 6000
Wire Wire Line
	3300 6000 3450 6000
Connection ~ 3450 6000
Wire Wire Line
	1750 5800 1900 5800
Wire Wire Line
	1900 6100 1900 6350
Wire Wire Line
	1900 6350 1250 6350
Wire Wire Line
	1250 6350 1250 5700
NoConn ~ 2000 2350
NoConn ~ 2000 2450
NoConn ~ 2000 2550
NoConn ~ 2000 2950
NoConn ~ 2000 3150
NoConn ~ 2000 3250
NoConn ~ 2000 3350
NoConn ~ 2000 3550
NoConn ~ 2000 3650
NoConn ~ 2000 3750
NoConn ~ 2000 3850
NoConn ~ 2000 3950
NoConn ~ 2000 4050
NoConn ~ 3200 4150
NoConn ~ 3200 4050
NoConn ~ 3200 3950
NoConn ~ 3200 3550
NoConn ~ 3200 3450
NoConn ~ 3200 3350
NoConn ~ 3200 3250
NoConn ~ 3200 3050
NoConn ~ 3200 2950
NoConn ~ 3200 2750
NoConn ~ 3200 2650
NoConn ~ 3200 2550
NoConn ~ 3300 6300
NoConn ~ 2000 2250
NoConn ~ 2000 3050
Wire Wire Line
	2000 5700 2000 4700
Wire Wire Line
	2000 4700 3950 4700
Wire Wire Line
	3950 4700 3950 2050
Wire Wire Line
	3950 2050 6500 2050
Connection ~ 6500 2050
Wire Wire Line
	1750 5700 2000 5700
$Comp
L actuators-rev2-rescue:PDQ15-Q24-S5-D-PDQ15-Q24-S5-D U2
U 1 1 5EBB76EE
P 2600 6000
F 0 "U2" H 2600 6567 50  0000 C CNN
F 1 "PDQ15-Q24-S5-D" H 2600 6476 50  0000 C CNN
F 2 "project_footprints:CONV_PDQ15-Q24-S5-D" H 2600 6000 50  0001 L BNN
F 3 "Manufacturer Recommendations" H 2600 6000 50  0001 L BNN
F 4 "1.0" H 2600 6000 50  0001 L BNN "Field4"
F 5 "CUI Inc" H 2600 6000 50  0001 L BNN "Field5"
	1    2600 6000
	1    0    0    -1  
$EndComp
Wire Wire Line
	1750 5700 1750 5800
Connection ~ 1750 5700
Wire Wire Line
	1250 5700 1400 5700
$Comp
L Device:CP1 C3
U 1 1 5ECD5BA5
P 1600 5850
F 0 "C3" H 1715 5896 50  0000 L CNN
F 1 "CP1" H 1715 5805 50  0000 L CNN
F 2 "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm" H 1600 5850 50  0001 C CNN
F 3 "~" H 1600 5850 50  0001 C CNN
	1    1600 5850
	1    0    0    -1  
$EndComp
Connection ~ 1600 5700
Wire Wire Line
	1600 5700 1750 5700
$Comp
L Device:CP1 C2
U 1 1 5ECD62C8
P 1400 5850
F 0 "C2" H 1515 5896 50  0000 L CNN
F 1 "CP1" H 1515 5805 50  0000 L CNN
F 2 "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm" H 1400 5850 50  0001 C CNN
F 3 "~" H 1400 5850 50  0001 C CNN
	1    1400 5850
	1    0    0    -1  
$EndComp
Connection ~ 1400 5700
Wire Wire Line
	1400 5700 1600 5700
Wire Wire Line
	1400 6000 1600 6000
Wire Wire Line
	1600 6000 1750 6000
Connection ~ 1600 6000
Connection ~ 1750 6000
Wire Wire Line
	4500 3150 5250 3150
Wire Wire Line
	6300 3150 7000 3150
Wire Wire Line
	6300 2850 7000 2850
Connection ~ 5250 2850
Wire Wire Line
	5250 2750 5250 2850
Connection ~ 5250 2750
Wire Wire Line
	5250 2850 4500 2850
Wire Wire Line
	6300 2850 6300 2750
Connection ~ 6300 2750
Connection ~ 6850 2950
$Comp
L Connector:Screw_Terminal_01x02 J2
U 1 1 5EBC53DC
P 7200 2850
F 0 "J2" H 7280 2842 50  0000 L CNN
F 1 "Screw_Terminal_01x02" H 7280 2751 50  0000 L CNN
F 2 "TerminalBlock:TerminalBlock_Altech_AK300-2_P5.00mm" H 7200 2850 50  0001 C CNN
F 3 "~" H 7200 2850 50  0001 C CNN
	1    7200 2850
	1    0    0    -1  
$EndComp
Wire Wire Line
	6850 2050 6850 2950
$EndSCHEMATC
