# Global Container Format implementation for Python

*pygcf* is a Python implementation of the [GCF format](https://github.com/moongoal/gcf-spec). It exposes a `gcf` package containing the tools required to read and write asset containers.

## Testing

To run the test, ensure you have the project's folder in your `PYTHONPATH` and the dependencies listed in the *requirements.txt* file installed; then run:

```bash
pytest test
```

To get a coverage report, run:

```bash
pytest --cov=gcf test
```

## Bugs and feedback

For bugs and feedback you can open an issue on the [GitHub repository](https://github.com/moongoal/pygcf).
