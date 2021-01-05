
birdfeeder
==========

Helper library for CoinAlpha projects

Installation
------------

To install library for development in conda environment, run

.. code-block::

   ./install

Alternativelly, you can use poetry env:

.. code-block::

   poetry install
   poetry shell

How to add a dependency
-----------------------


#. If you're running in conda, you need to install required package first.
#. Then, see installed version in ``conda env export``
#. Take this version and add into pyproject.toml, into ``[tool.poetry.dependencies]`` (or dev section, if the package is needed for development only). Specify version (or range) according to `Dependency Specification <https://python-poetry.org/docs/dependency-specification/>`_

If using poetry:


#. Run ``poetry add <package>``

Releasing a new version
-----------------------


#. Change version in ``pyproject.toml``
#. Generate ``setup.py``
#. Generate ``environment.yml``

Generate ``setup.py``\ :

.. code-block::

   dephell deps convert

Generate conda ``environment.yml``\ :

.. code-block::

   poetry2conda --dev pyproject.toml environment.yml
