.. _controller_overview:

Controller
=================


Purpose of the Controller
----------

.. image:: /images/single_waveform.png
   :width: 100%
   :alt: Single Waveform 

Shown above is a typical respiratory waveform without smoothing, as produced with PVP1. Blue is the pressue recorded. during inspiration, orange is the flow out of the system. Note that airflow (and also oxygen concentration) are only measured during expiration, so that the main control-loop during inspiration runs as fast as possible, and is not slowed down by communication delays. Empirically, the Raspberry pi allowed for the primary control loop to run at speeds  of ~5ms per loop, which was considerably faster than all hardware delays (i.e. the time it takes for a mechanical, physical valve to open or close; see main manuscript).

The purpose of the controller is to produce a breath waveform, as the one shown above. More specifically, it's job is to reach a certain target-pressure (PIP), and to hold that preassure for a certain amount of time. These numbers are provided by the user. Exhalation is passive, and PEEP pressure is mechanically controlled with a spring-valve. 

Conceptually, the controller is written as a hybrid system of state and PID control. During inspiration, it actively  controls pressure with a simple PID system. That means that during inspiration, it measures the deviation of the pressure-is-vale from the pressure-target-value, and depending an that distance (and its integral and derivative), it adjusts the opening of the inspiratory valve. Expiration was then instantiated by closing the inpiratory, and opening the expiratory valve to passively release PIP pressure as fast as possible. After reaching PEEP, the controller opens the inspiratory valve slightly to sustain a small flow during PEEP, using the aforementioned manually operated PEEP-valve. We found, empirically, that a combination of proportional and integral term worked best across different physical lung settings.

In addition, we allow the user to adjust flow through the system. This is done by a linear correction of the proportional-term, and adjusts rise-time depending on the user's inputs.

In  addition  to  pressure  control,  our  software  continuouslymonitors  for  autonomous  breaths,   high  airway  pressure,and  general  system  status.Autonomous  breathing  wasdetected by transient pressure drops below PEEP. A detectedbreath triggered a new breath cycle.   High airway pressureis defined as exceeding a certain pressure for a certain time(as to not be triggered by a cough).  This triggered an alarm,and  an  immediate  release  of  air  to  drop  pressure  to  PEEP.The  Controller  also  assesses  whether  numerical  values  arereasonable, and changing over time.  If this is not the case,it  raises  an  technical  alarm.   All  alarms  are  collected  andmaintained by an intelligent alarm manager, that provides theUI with the alarms to display in order of their importance.In  addition  to  the  alarm  system,  the  controller  monitorsfor autonomous breath events during peep.  We define suchevents by a drop below the PEEP baseline exceeding somefixed  threshold.   If  an  autonomous  drop  was  detected,  thenext breath cycle is initiated

And it calculates VTE:

Architecture of the Controller
----------

In terms of software components, the Controller consists of one main :class:`~.pvp.controller` object that receives sensor-data, and computes control parameters, to change the machanical position of valves. The controller receives ventilation control parameters (see :meth:`~.PVP_Gui.set_control`), and continuously computes new valve-setting. This is done it is own thread. All exchanged variables are mutex'd.

The Controller also feeds the :class:`.Logger` :class:`.SensorValues` objects so that it can store high-temporal resolution data.

The main **control loop** is :meth:`.pvp.controller._start_mainloop()` which queries the Hardware for new variables, and performs a PID update using `.pvp.controller._PID_update()`.

The Controller is **configured** by the :mod:`~.common.values` module, 


The Controller can be launched alone, but was not intended to be launched alone.

.. automodule:: pvp.controller.control_module
   :members:
   :undoc-members:
   :show-inheritance:



