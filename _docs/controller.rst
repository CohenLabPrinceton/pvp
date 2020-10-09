.. _controller_overview:

Controller
=================


Purpose of the Controller
----------

.. image:: /images/single_waveform.png
   :width: 100%
   :alt: Raw data for a single breath; blue is pressure and orange is flow-out.

Shown above is a typical respiratory waveform (without averaging) as produced with PVP1. Blue is the recorded pressure, orange is the flow out of the system. Note that airflow (and also oxygen concentration) are only measured during expiration, so that the main control-loop during inspiration runs as fast as possible, and is not slowed down by communication delays. Pressure is recorded continuously. Empirically, the Raspberry pi allowed for the primary control loop to run at speeds of ~5ms per loop, which was considerably faster than all hardware delays (i.e. the time it takes for a mechanical, physical valve to open or close; see main manuscript).

The purpose of the controller is to produce a breath waveform, as the one shown above. More specifically, it's job is to reach a certain target-pressure (PIP), and to hold that pressure for a certain amount of time. These numbers are provided by the user via thee UI. Exhalation is passive, and PEEP pressure is mechanically controlled with a spring-valve.

Conceptually, the controller is written as a hybrid system of state and PID control. During inspiration, it actively controls pressure with a simple `PID controller <https://en.wikipedia.org/wiki/PID_controller>`_. That means that during inspiration, it measures the deviation of the pressure-is-vale from the pressure-target-value, and depending an that distance (and its integral and derivative), it adjusts the opening of the inspiratory valve. Expiration was then instantiated by closing the inspiratory, and opening the expiratory valve to passively release PIP pressure as fast as possible. After reaching PEEP, the controller opens the inspiratory valve slightly to sustain a small flow during PEEP, using the aforementioned manually operated PEEP-valve. We found, empirically, that a combination of proportional and integral term worked best across different physical lung settings.

The controller was also built to allow the user to adjust flow through the system. This is done by a linear correction of the proportional-term. With this adjustment, the user can  manipulate the rise-time of the pressure waveform.

In addition to this core function, the controller module continuously monitors for autonomous breaths, high airway pressure, and general system status. Autonomous breathing was detected by transient pressure drops below PEEP. A detected breath triggered a new breath cycle. High airway pressure is defined as exceeding a certain pressure for a certain time (as to not be triggered by a cough). This event triggered an alarm, and  an immediate release of air to drop to a safe pressure and not to exceed PIP. Both of these functionalities are fast, and respond, at the latest, within few hundred milliseconds. The controller also assesses whether numerical values and sensor readings are reasonable, and changing over time. If this is not the case, it raises an technical alarm. All alarms are collected and maintained by an intelligent alarm manager, that provides the UI with the alarms to display in order of their importance. 

The final functionality of the control module is the estimation of VTE (VTE stands for exhaled tidal volume), which is thee volume of air that made it in- and out of the lung. We estimate this number by integrating the expiratory flow during expiration, and subtracting the baseline flow used to sustain PEEP (details in the accompanying manuscript):

Architecture of the Controller
----------

In terms of software components, the Controller consists of one main :class:`~.pvp.controller` class, that is instantiated in its own thread. This object receives sensor-data from HAL, and computes control parameters, to change the mechanical position of valves. The Controller also receives ventilation control parameters (see :meth:`~.PVP_Gui.set_control`). All exchanged variables are mutex'd.

The Controller also feeds the :class:`.Logger` a continuous stream of :class:`.SensorValues` objects so as to store high-temporal resolution data, including the control signals.

The main **control loop** is :meth:`.pvp.controller._start_mainloop()` which queries the Hardware for new variables, and performs a PID update using `.pvp.controller._PID_update()`.

The Controller is **configured** by the :mod:`~.common.values` module, 

The Controller can be launched alone, but was not intended to be launched alone. The alarm functionality requires the UI.

.. automodule:: pvp.controller.control_module
   :members:
   :undoc-members:
   :show-inheritance:



