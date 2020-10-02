.. _controller_overview:

Controller
=================


Screenshot
----------

.. image:: /images/single_waveform.png
   :width: 100%
   :alt: Single Waveform 

The Controller consists of one main :class:`~.pvp.controller` object that receives sensor-data, and computes control parameters, to change valve settings. The controller receives ventilation control parameters (see :meth:`~.PVP_Gui.set_control`), and can provide the currently active set of controls (see???)

The Controller also feeds the :class:`.Logger` :class:`.SensorValues` objects so that it can store high-temporal resolution data.

The main **polling loop** of the Controller is :meth:`.PVP_Gui.update_gui` which queries the Hardware for new variables, that are wired up in a new :class:`.SensorValues` and distributes
them to all listening widgets (see method documentation for more details).

The Controller is **configured** by the :mod:`~.common.values` module, in particular it creates

* :class:`~.widgets.display.Display` widgets in the left "sensor monitor" box from all :class:`~.common.values.Value` s in :data:`~.values.DISPLAY_MONITOR` ,

The Controller can be launched alone::


but was not intended to be launched alone.

add logging

.. automodule:: pvp.controller.control_module
   :members:
   :undoc-members:
   :show-inheritance:



Control  into  a  breathing  cycle  was  accomplished  with  ahybrid system of state and PID control.  During inspiration,we  actively  control  pressure  using  a  PID  cycle  to  set  theinspiratory valve. Expiration was then instantiated by closingthe inpiratory, and opening the expiratory valve to passivelyrelease PIP pressure as fast as possible. After reaching PEEP,we  opened  the  inspiratory  valve  slightly  to  sustain  PEEPusing  the  aforementioned  manually  operated  PEEP-valveand to sustain a gentle flow of air through the system


The  Raspberry  pi  allowed  for  the  primary  control  loop  torun  at  speeds  exceeding≈320Hz,  using≈40%of  themaximum   bandwidth   of   the   analog-to-digital   converterreading the sensors

In  addition  to  pressure  control,  our  software  continuouslymonitors  for  autonomous  breaths,   high  airway  pressure,and  general  system  status.Autonomous  breathing  wasdetected by transient pressure drops below PEEP. A detectedbreath triggered a new breath cycle.   High airway pressureis defined as exceeding a certain pressure for a certain time(as to not be triggered by a cough).  This triggered an alarm,and  an  immediate  release  of  air  to  drop  pressure  to  PEEP.The  Controller  also  assesses  whether  numerical  values  arereasonable, and changing over time.  If this is not the case,it  raises  an  technical  alarm.   All  alarms  are  collected  andmaintained by an intelligent alarm manager, that provides theUI with the alarms to display in order of their importance.In  addition  to  the  alarm  system,  the  controller  monitorsfor autonomous breath events during peep.  We define suchevents by a drop below the PEEP baseline exceeding somefixed  threshold.   If  an  autonomous  drop  was  detected,  thenext breath cycle is initiated