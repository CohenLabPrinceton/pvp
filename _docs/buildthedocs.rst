Building the Docs
==================

A very brief summary...

* Docs are configured to be built from ``_docs`` into ``docs``.
* The main page is ``index.rst`` which links to the existing modules
* To add a new page, you can create a new ``.rst`` file if you are writing with Restructuredtext_ , or a `.md` file if you are writing with markdown.


Local Build
-----------

* ``pip install -r requirements.txt``
* ``cd _docs``
* ``make html``

Documentation will be generated into ``docs``



.. _Restructuredtext: https://docutils.sourceforge.io/docs/user/rst/quickref.html