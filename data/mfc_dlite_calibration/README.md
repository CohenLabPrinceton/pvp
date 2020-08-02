This data was collected by Philippe Bourrianne (Princeton MAE) and processed by Sophie Dvali (Princeton Physics). 

A mass-flow controller (MFC) was set to output varying rates of flow to a D-Lite spirometer (with a differential pressure sensor attached). 
Voltage data was collected from the differential pressure sensor as the flow varied. Pressure readings from the D-Lite were logged as well.

TV_1 (10 steps from 10 to 100 L/min - 2 successive ramps down and up - physics classical protocol for calibration) (atmospheric pressure at the output of the Flow Block)

TV_2 (10 steps from 10 to 100 L/min - 2 successive ramps down and up - physics classical protocol for calibration) (atmospheric pressure at the output of the Flow Block)

TV_finecalib_1 (many steps from 1 to 100 L/min - for a more detailled calibration - useful to investigate the functional form of a fit) (atmospheric pressure at the output of the Flow Block)

TV_Peep3D_1 (10 steps from 10 to 100 L/min - 2 successive ramps down and up - physics classical protocol for calibration) (3D printed PEEP valve at the output of the Flow Block)

TV_Peepcm10_1 (10 steps from 10 to 100 L/min - 2 successive ramps down and up - physics classical protocol for calibration) (10cmH20 PEEP valve at the output of the Flow Block)

For each test, you have 3 csv files:

i) one ending by ‘_Q.csv’: synchronized data
the first column is time (in s), the second is the order on flow-rate (in L/min) and the third column is the actual flow-rate provided by the mass flow controller (in L/min).

ii) one ending by ‘_DP.csv’: synchronized data
the first column is the time (in s) and the second is the differential pressure DeltaP (from dlite_voltage.csv), and the third is the absolute pressure (from pressure_log.csv).

iii) one ending by ‘_Ave.csv’: averaged data
first column: mean(Q) (in L/min) per step of constant flow-rate
second column: standard deviation of Q (in L/min) per step
third column: mean(DeltaP) (in Pa) per step
fourth column: standard deviation(DeltaP) (in Pa) per step
