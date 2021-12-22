Unit Conversion
================

Functions that convert between units

Each function should accept a single float as an argument and return a single float

Used by the GUI to display values in different units. Widgets use these as

* ``_convert_in`` functions to convert units from the base unit to the displayed unit and
* ``_convert_out`` functions to convert units from the displayed unit to the base unit.

.. note::

    Unit conversions are cosmetic -- values are always kept as the base unit internally (ie. cmH2O for pressure)
    and all that is changed is the displayed value in the GUI.

.. automodule:: pvp.common.unit_conversion
   :members:
   :undoc-members:
   :show-inheritance: