# Global Container Format implementation for Python

*pygcf* is a Python implementation of the [GCF format](https://github.com/global-container-format/gcf-spec). It exposes a `gcf` package containing the tools required to read and write asset containers.

## Building

To build the distribution packages, ensure the dependencies listed in the *requirements.txt* file are installed and then run:

```bash
python -mbuild
```

This will create and populate a *dist/* folder.

## Testing

To run the test, ensure you have the project's folder in your `PYTHONPATH` and the dependencies listed in the *requirements.txt* file installed; then run:

```bash
pytest test
```

To get a coverage report, run:

```bash
pytest --cov=gcf test
```

## Development

The toolchain used by this project is:

* pipenv (assumed to be already installed)
* pytest
* isort
* pylint
* black
* mypy

To install the development tools, run

```bash
# Create new environment
pipenv --python 3

# Install dependencies, including dev dependencies
pipenv install -d
```

To run the tools

```bash
# Sort imports
isort .

# Format
black .

# Lint
pylint gcf

# Validate typing
mypy gcf
```

### Documentation

PyGCF's documentation is built via Sphinx. To build the documentation, run:

```bash
sphinx-build -b html doc dist/doc
```

## License

See the [LICENSE](LICENSE) file.


## Bugs and feedback

For bugs and feedback you can open an issue on the [GitHub repository](https://github.com/moongoal/pygcf).
