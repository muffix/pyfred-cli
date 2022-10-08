# Contributor guidelines

Thank you for considering a contribution to `pyfred`.

The main goal of this project is to facilitate building Alfred workflows without having to worry about the setup and
distribution. It should be easy to bootstrap a new workflow, the code should be editable in the author's favourite IDE
or editor, and it should require the least amount of work possible to test code changes.

The main requirement for contributions are that they work with the latest version of macOS and Alfred, and do not mess
with the system Python interpreter.

Please fork this repository and create a pull request back to this one so that it can be reviewed.

## Dependencies

There are three requirements files:

- `requirements.txt` for dependencies needed at runtime
- `requirements-test.txt` for dependencies needed to run the tests
- `requirements-doc.txt` for dependencies needed to build the documentation

New dependencies should be added to these files where needed.

## Installing pre-commit hooks

The project comes with a [pre-commit](https://pre-commit.com/) configuration which automatically performs some basic
checks before committing. The hooks need to be installed once with `pre-commit install`.

## Tests

New functionality should be covered with tests where possible. See the `pyalfred.tests` module for examples.

To run the tests, just run `pytest`.

## Mypy

There is a job in GitHub actions (and a pre-commit hook) making sure that changed Python files all pass
[mypy](https://github.com/python/mypy) checks. Please add type hints to new methods and make sure the code passes the
checks.
