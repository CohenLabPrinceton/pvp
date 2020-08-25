Performance
=================

.. figure:: /images/single_waveform.png
    :align: center
    :figwidth: 100%
    :width: 100%

    Representative pressure control breath cycle waveforms for airway pressure and flow out. Test settings: compliance C=20 mL/cm H2O, airway resistance R=20 cm H2O/L/s, PIP=30 cm H2O, PEEP=5 cm H2O.

The completed system was tested with a standard test lung (QuickLung, IngMar Medical, Pittsburgh, PA)
that allowed testing combinations of three lung compliance settings (C=5, 20, and 50 mL cm H2O) and
three airway resistance settings (R=5, 20, and 50 cm H2O/L/s). The figure above shows pressure control 
performance for midpoint settings: C=20 mL/cm H2O, R=20 cm H2O/L/s, PIP=30 cm H2O, PEEP=5 cm H2O. 
PIP is reached within a 300 ms ramp period, then holds for the PIP plateau with minimal fluctuation 
of airway pressure for the remainder of the inspiratory cycle (blue). One the expiratory valve opens, 
exhalation begins and expiratory flow is measured (orange) as the airway pressure drops to PEEP and remains
 there for the rest of the PEEP period. 
 
.. figure:: /images/tune_waveform.png
    :align: center
    :figwidth: 100%
    :width: 100%
	
	Demonstration of waveform tuning via flow adjustment. If desired, the operator can increase the flow setting through the system GUI to decrease the pressure ramp time. Test settings: compliance C=20 mL/cm H2O, airway resistance R=20 cm H2O/L/s, PIP=30 cm H2O, PEEP=5 cm H2O. 
 
Some manual adjustment of the pressure waveforms may be warranted depending on the patient, and such adjustment is permitted through a user flow adjustment setting. This flow adjustment setting allows the user to increase the maximum flow rate during the ramp cycle to inflate lungs with higher compliance. The flow setting can be readily changed from the GUI and the control system immediately adapts to the user's input. An example of this flow adjustment is shown in the figure above for four breath cycles. While all cycles reach PIP, the latter two have a higher mean airway pressure, which may be more desirable under certain conditions than the lower mean airway pressure of the former two.


ISO Standards Testing
-----------------------

In order to characterize the PVP's control over a wide range of conditions, we followed FDA Emergency Use Authorization guidelines,
which specify ISO 80601-2-80-2018 for a battery of pressure controlled ventilator standard tests.
We tested the conditions that do not stipulate a leak, and present the results here.
For each configuration the following parameters are listed: the test number (from the table below),
the compliance (C, mL/cm H2O), linear resistance (R, cm H2O/L/s), respiratory frequency (f, breaths/min), peak inspiratory pressure (PIP, cm H2O), positive end-expiratory pressure (PEEP, cm H2O), and flow adjustment setting.

.. csv-table:: Standard test battery from Table 201.105 in ISO 80601-2-80-2018 for pressure controlled ventilators
   :file: assets/csv/eua_test.csv
   :widths: 3,5,5,5,5,5,5,5,5
   :header-rows: 1

.. figure:: /images/waveform_battery_500mL.png
    :align: center
    :figwidth: 100%
    :width: 100%
	
	Performance results of the ISO 80601-2-80-2018 pressure controlled ventilator standard tests with an intended delivered tidal volume of 500 mL. For each configuration the following parameters are listed: the test number (from table 201.105 in the ISO standard), the compliance (C, mL/cm H2O), linear resistance (R, cm H2O/L/s), respiratory frequency (f, breaths/min), peak inspiratory pressure (PIP, cm H2O), positive end-expiratory pressure (PEEP, cm H2O), and flow adjustment setting. PIP is reached in every test condition except for case 2, which is approximately 2.4 cm H2O below the set point.

.. figure:: /images/waveform_battery_300mL.png
    :align: center
    :figwidth: 100%
    :width: 100%
	
	Performance results of the ISO 80601-2-80-2018 pressure controlled ventilator standard tests with an intended delivered tidal volume of 300 mL. For each configuration the following parameters are listed: the test number (from table 201.105 in the ISO standard), the compliance (C, mL/cm H2O), linear resistance (R, cm H2O/L/s), respiratory frequency (breaths/min), peak inspiratory pressure (PIP, cm H2O), positive end-expiratory pressure (PEEP, cm H2O), and flow adjustment setting. PIP is reached in every test condition.

These tests cover an array of conditions,
and more difficult test cases involve a high airway pressure coupled with a low lung compliance (case nos. 8 and 9).
Under these conditions, if the inspiratory flow rate during the ramp phase is too high, 
the high airway resistance will produce a transient spike in airway pressure which can greatly overshoot the PIP value.
For this reason, the system uses a low initial flow setting and allows the clinican to increase the flow rate if necessary.

.. figure:: /images/tidal_volumes.png
    :align: center
    :figwidth: 100%
    :width: 100%

	Tidal volume performance for the ISO 80601-2-80-2018 pressure controlled ventilator standard tests, averaged across 30 breath cycles for each condition.

The PVP integrates expiratory flow to monitor the tidal volume, which is not directly set in pressure controlled ventilation, but is an important parameter. Of the test conditions in the ISO standard, four that we tested intended a nominal delivered tidal volume of 500 mL, three intended 300 mL, and one intended 200 mL. For most cases, the estimated tidal volume has a tight spread clustered within 10% of the intended value.

Breath Detection
------------------

.. figure:: /images/spontaneous_breath.png
    :align: center
    :figwidth: 100%
    :width: 100%
	
	Spontaneous breath detection.
	
A patient-initiated breath after exhalation will result in a momentary drop in PEEP. PVP may optionally detect these transient decreases to trigger a new pressure-controlled breath cycle. We tested this functionality by triggering numerous breaths out of phase with the intended inspiratory cycle, using a QuickTrigger (IngMar Medical, Pittsburgh, PA) to momentarily open the test lung during PEEP and simulate this transient drop of pressure.

High Pressure Detection
--------------------------

.. figure:: /images/hapa_demonstration.png
    :align: center
    :figwidth: 100%
    :width: 100%
	
	High pressure alarm demonstration.
	
Above is a demonstration of the PVP's high airway pressure alarm (HAPA). An airway blockage results in a high airway pressure (above 60 cm H2O) that the system corrects within ~500 ms.
Test settings: compliance C=20 mL/cm H2O, airway resistance R=20 cm H2O/L/s, PIP=30 cm H2O, PEEP=5 cm H2O.