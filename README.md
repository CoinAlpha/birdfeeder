# birdfeeder

Helper library for CoinAlpha projects

## Installation

To install library for development in conda environment, run

```
./install
```

Alternativelly, you can use poetry env:

```
poetry install
poetry shell
```

## How to add a dependency

1. If you're running in conda, you need to install required package first.
1. Then, see installed version in `conda env export`
1. Take this version and add into pyproject.toml, into `[tool.poetry.dependencies]` (or dev section, if the package is needed for development only). Specify version (or range) according to [Dependency Specification](https://python-poetry.org/docs/dependency-specification/)

If using poetry:

1. Run `poetry add <package>`

## Releasing a new version

1. Change version in `pyproject.toml`
1. Generate `setup.py`
1. Generate `environment.yml`


Generate `setup.py`:

```
dephell deps convert
```

Generate conda `environment.yml`:

```
poetry2conda --dev pyproject.toml environment.yml
```
