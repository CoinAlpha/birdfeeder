
birdfeeder
==========

Helper library for CoinAlpha projects

Usage
-----

The library is not (yet?) published to pypi.

In pyproject.toml:

.. code-block::

   birdfeeder = { git = "https://github.com/coinalpha/birdfeeder.git", branch = "master" }
   birdfeeder = { git = "https://github.com/coinalpha/birdfeeder.git", rev = "29cdd7229d0d35a989322f5026382400d1332da4" }
   birdfeeder = { git = "https://github.com/coinalpha/birdfeeder.git", tag = "0.1.0" }

pip:

.. code-block::

   git+https://github.com/coinalpha/birdfeeder.git@master#egg=birdfeeder
   git+https://github.com/coinalpha/birdfeeder.git@29cdd7229d0d35a989322f5026382400d1332da4#egg=birdfeeder
   git+https://github.com/coinalpha/birdfeeder.git@0.1.0#egg=birdfeeder

Development
-----------

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

Idea: we're keeping own version and dependencies info in ``pyproject.toml``\ , and then generating ``setup.py`` so that the library could be installed via tools like pip. We're also generating ``environment.yml`` file because we're mostly using conda to manage development environments at CoinAlpha.


#. Change version in ``pyproject.toml``
#. Generate ``setup.py``\ : ``dephell deps convert``
#. Generate ``environment.yml``\ : ``poetry2conda --dev pyproject.toml environment.yml``
#. Commit updates ``git add -u && git commit``
#. Create git tag ``x.y.z``\ : ``git tag x.y.z``
#. Run ``git push && git push --tags``
