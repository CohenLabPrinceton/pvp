.. _gui_overview:

GUI
======

.. toctree::
   :hidden:
   :maxdepth: 4

   PVP GUI <main>
   Widgets <widgets/index>
   Stylesheets <styles>


.. raw:: html
   :file: assets/images/pvp_gui_overview_clickable.svg

The GUI is written using `PySide2 <https://wiki.qt.io/Qt_for_Python>`_ and consists of one main :class:`~.gui.main.PVP_Gui`
object that instantiates a series of :ref:`gui_widgets`. The GUI is responsible for setting ventilation control parameters
and sending them to the :mod:`~pvp.controller` (see :meth:`~.PVP_Gui.set_control`), as well as receiving and displaying sensor values (:meth:`~.ControlModuleBase.get_sensors`).

The GUI also feeds the :class:`.Alarm_Manager` :class:`.SensorValues` objects so that it can compute alarm state. The :class:`.Alarm_Manager`
reciprocally updates the GUI with :class:`.Alarm` s (:meth:`.PVP_Gui.handle_alarm`) and Alarm limits (:meth:`.PVP_Gui.limits_updated`).

The main **polling loop** of the GUI is :meth:`.PVP_Gui.update_gui` which queries the controller for new :class:`.SensorValues` and distributes
them to all listening widgets (see method documentation for more details). The rest of the GUI is event driven, usually with Qt
Signals and Slots.

The GUI is **configured** by the :mod:`~.common.values` module, in particular it creates

* :class:`~.widgets.display.Display` widgets in the left "sensor monitor" box from all :class:`~.common.values.Value` s in :data:`~.values.DISPLAY_MONITOR` ,
* :class:`~.widgets.display.Display` widgets in the right "control" box from all :class:`~.common.values.Value` s in :data:`~.values.DISPLAY_CONTROL` , and
* :class:`~.widgets.plot.Plot` widgets in the center plot box from all :class:`~.common.values.Value` s in :data:`~.values.PLOT`

The GUI is not intended to be launched alone, as it needs an active :mod:`~pvp.coordinator` to communicate with the controller process
and a few prelaunch preparations (:func:`~.gui.main.launch_gui`). PVP should be started like::

    python3 -m pvp.main

Module Overview
----------------

.. raw:: html

    <div class="software-summary">
        <a href="gui.main.html"><h2>PVP_Gui</h2></a> <p>Main GUI Object that controls all the others!</p>
        <a href="gui.widgets.html"><h2>Widgets</h2></a> <p>Widgets used by main GUI</p>
        <a href="gui.styles.html"><h2>IO</h2></a> <p>Stylesheets used by the GUI</p>
    </div>

Screenshot
----------

.. image:: /images/gui_overview_v1_1920px.png
   :width: 100%
   :alt: Gui Overview - modular design, alarm cards, multiple modalities of input, alarm limits represented consistently across ui






