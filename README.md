# birdfeeder

Helper library for CoinAlpha projects

## Usage

The library is published to pypi as [birdfeeder-coinalpha](https://pypi.org/project/birdfeeder-coinalpha/)

### Installing

```
pip install birdfeeder-coinalpha
```

```
poetry add 'birdfeeder-coinalpha@^1'
```


### How to install old versions

In pyproject.toml:

```
birdfeeder-coinalpha = { git = "https://github.com/coinalpha/birdfeeder.git", branch = "master" }
birdfeeder-coinalpha = { git = "https://github.com/coinalpha/birdfeeder.git", rev = "29cdd7229d0d35a989322f5026382400d1332da4" }
birdfeeder-coinalpha = { git = "https://github.com/coinalpha/birdfeeder.git", tag = "0.1.0" }
```

pip:

```
git+https://github.com/coinalpha/birdfeeder.git@master#egg=birdfeeder
git+https://github.com/coinalpha/birdfeeder.git@29cdd7229d0d35a989322f5026382400d1332da4#egg=birdfeeder
git+https://github.com/coinalpha/birdfeeder.git@0.1.0#egg=birdfeeder
```


## Development

To install library for development in conda environment, run

```
./install
```

Alternativelly (preferred), you can use poetry env:

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

Idea: we're keeping own version and dependencies info in `pyproject.toml`, and then generating `setup.py` so that the library could be installed via tools like pip. We're also generating `environment.yml` file because we're mostly using conda to manage development environments at CoinAlpha.

1. Change version in `pyproject.toml` and `birdfeeder/__init__.py`
1. Generate `setup.py`: `dephell deps convert`
1. Generate `environment.yml`: `poetry2conda --dev pyproject.toml environment.yml`
1. Commit updates `git add -u && git commit`
1. Create git tag `x.y.z`: `git tag -s x.y.z`
1. Run `git push && git push --tags`
1. Publish to pypi: `poetry publish --build`
