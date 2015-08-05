.. _parsetron_index:

.. Parsetron documentation master file, created by
   sphinx-quickstart on Mon Apr 13 12:36:49 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. role:: text-success
.. role:: text-primary
.. role:: text-info
.. role:: text-warning
.. role:: text-danger

.. role:: bg-success
.. role:: bg-primary
.. role:: bg-info
.. role:: bg-warning
.. role:: bg-danger


***********************************
Parsetron, a Robust Semantic Parser
***********************************

.. topic:: Abstract

   Parsetron is a robust incremental natural language parser utilizing semantic
   grammars for small focused domains. It is mainly used to convert natural
   language command to executable API calls (e.g.,
   *"set my bedroom light to red"* --> ``set_light('bedroom', [255, 0, 0])``).
   Parsetron is written in pure Python (2.7), portable (a single
   ``parsetron.py`` file), and can be used in conjunction with a speech
   recognizer.

:License: Apache License 2.0

:Author: Xuchen Yao from `KITT.AI <http://kitt.ai>`_

:Source: https://github.com/Kitt-AI/parsetron

:Release: v0.1.1

.. rubric:: Table of Contents

.. toctree::
   :maxdepth: 3

   quickstart
   tutorial
   advanced
   api



.. Adding disqus and google analytics:
    For sample syntax, refer to:
    https://pythonhosted.org/an_example_pypi_project/sphinx.html
    https://docs.python.org/devguide/documenting.html
    http://eseth.org/2010/blogging-with-sphinx.html
    https://github.com/whiteinge/eseth/blob/master/templates/layout.html#L151


.. Indices and tables
    ==================
    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`

