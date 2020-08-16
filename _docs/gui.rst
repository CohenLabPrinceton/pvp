GUI
======



GUI Overview
---------------

Design
~~~~~~~~~~~~~~~~~~~~

.. raw:: html
   :file: assets/images/pvp_gui_overview_clickable.svg

The GUI is written using `PySide2 <https://wiki.qt.io/Qt_for_Python>`_ and consists of one main :class:`~.gui.main.PVP_Gui`
object that instantiates a series of :mod:`~.gui.widgets`. The GUI is responsible for setting ventilation control parameters
and sending them to the :mod:`~pvp.controller` (see :meth:`~.PVP_Gui.set_control`), as well as receiving and displaying sensor values (:meth:`~.ControlModuleBase.get_sensors`).

The GUI also feeds the :class:`.Alarm_Manager` :class:`.SensorValues` objects so that it can compute alarm state. The :class:`.Alarm_Manager`
reciprocally updates the GUI with :class:`.Alarm` s (:meth:`.PVP_Gui.handle_alarm`) and Alarm limits (:meth:`.PVP_Gui.limits_updated`).

The main polling loop of the GUI is :meth:`.PVP_Gui.update_gui` which queries the controller for new :class:`.SensorValues` and distributes
them to all listening widgets (see method focumentation for more details). The rest of the GUI is event driven, usually with Qt
Signals and Slots.

The GUI is configured by the :mod:`~.common.values` module, in particular it creates

* :class:`~.widgets.display.Display` widgets in the left "sensor monitor" box from all :class:`~.common.values.Value` s in :data:`~.values.DISPLAY_MONITOR` ,
* :class:`~.widgets.display.Display` widgets in the right "control" box from all :class:`~.common.values.Value` s in :data:`~.values.DISPLAY_CONTROL` , and
* :class:`~.widgets.plot.Plot` widgets in the center plot box from all :class:`~.common.values.Value` s in :data:`~.values.PLOT` 

The GUI is not intended to be launched alone, as it needs an active :mod:`~pvp.coordinator` to communicate with the controller process
and a few prelaunch preparations (:func:`~.gui.main.launch_gui`). PVP should be started like::

    python3 -m pvp.main

Module Overview
~~~~~~~~~~~~~~~~

.. raw:: html

    <div class="software-summary">
        <a href="gui.html"><h2>GUI</h2></a> <p>A modular GUI with intuitive controls and a clear alarm system that can be configured to control any parameter or display values from any sensor.</p>
        <a href="controller.html"><h2>Controller</h2></a> <p>... Manuel write this</p>
        <a href="io.html"><h2>IO</h2></a> <p>A hardware abstraction layer powered by <a href="http://abyz.me.uk/rpi/pigpio/">pigpio</a> that can read/write at [x Hz]</p>
        <a href="alarm.html"><h2>Alarm</h2></a> <p>Define complex and responsive alarm triggering criteria with human-readable Alarm Rules</p>
        <a href="common.html"><h2>Common</h2><a> <p>Modules that provide the API between the GUI and controller, user preferences, and other utilities</p>
    </div>

Screenshot
~~~~~~~~~~~

.. image:: /images/gui_overview_v1_1920px.png
   :width: 100%
   :alt: Gui Overview - modular design, alarm cards, multiple modalities of input, alarm limits represented consistently across ui


.. toctree::
   :hidden:
   :maxdepth: 4

   PVP GUI <gui.main>
   Widgets <gui.widgets>
   Stylesheets <gui.styles>



