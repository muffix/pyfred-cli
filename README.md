# Pyfred

`pyfred` helps you create [Alfred](https://www.alfredapp.com/) workflows in Python. It has been heavily inspired by a
similar project for Rust, [powerpack](https://github.com/rossmacarthur/powerpack).

It comes with a CLI that helps bootstrapping, maintaining and packaging the workflow.

Dependencies are vendored and packaged with the workflow so that they don't need to be installed into the system Python.
See the [section on adding dependencies](#adding-dependencies) for details.

## Documentation

The documentation is deployed to [GitHub pages](https://muffix.github.io/pyfred-cli).

## Installation

You can install directly from PyPI:

```shell
pip install pyfred-cli
```

## Using the CLI

The CLI knows four commands: `new`, `link`, `package`, `vendor`.

See `pyfred {new,vendor,link,package} -h` for detailed help.

### New

Bootstraps a new workflow with a single script filter and links it into Alfred.

It creates a new directory with the given name and copies a "Hello Alfred" workflow there.
The workflow can be used immediately by invoking Alfred with the specified keyword.

The following example creates a `hello` directory containing a workflow that can be triggered with the `hi` keyword. The
result of the selected action is copied to the clipboard.

```shell
pyfred new hello -k hi -b de.muffix.helloalfred --author=Muffix --description="Hello Alfred".
```

### Link

Executed from a directory bootstrapped by this CLI, it links or relinks the workflow into Alfred.

```shell
pyfred link
```

### Vendor

Downloads the dependencies listed in the `requirements.txt` file and vendors them into the `workflow/vendored`
directory. Doing this avoids having to install them into the system Python interpreter.

```shell
pyfred vendor
```

### Package

Packages the workflow into a `*.alfredworkflow` file in the `dist` directory. The file contains the entire workflow and
all dependencies. It can be distributed and imported.

```shell
pyfred package
```

### Debug output

The CLI will log debug output if the `--debug` flag is passed before the command.

## Creating a workflow

The classes from the `pyfred.model` module represent the output expected by Alfred from a script filter.

`pyfred.workflow` provides a decorator for the entry point of a filter. It preprocesses the input and serialises the
response to stdout, where it is being picked up by the next input.

A minimal example for a script filter workflow looks like this:

```python
from pyfred.model import Environment, OutputItem, ScriptFilterOutput
from pyfred.workflow import script_filter

@script_filter
def main(script_path: Path, args_from_alfred: list[str], env: Optional[Environment]) -> ScriptFilterOutput:
    return ScriptFilterOutput(items=[OutputItem(title="Hello Alfred!")])
```

## Adding dependencies

When running the workflow, Alfred will use the system Python interpreter to run the script. Third-party libraries are
not available in the interpreter unless explicitly installed. In order to not pollute the system Python, dependencies
can be vendored with the workflow using the `pyfred vendor` command. It is also automatically run with `pyfred package`.

If you add dependencies to your `requirements.txt` file, you need to run `pyfred vendor` to download them. You do _not_
need to prefix the import with `vendored` because the template adds that directory to the `PYTHONPATH` variable when the
workflow runs.

## IDE setup

If you're using an IDE like PyCharm, you'll want to open the generated directory and set up the `workflow` subdirectory
as the content root. Additionally, you should add the `workflow/vendored` directory as source directory in the PyCharm
project settings. This helps it resolve the imports correctly.

## Adding icons

You can add an icon for your workflow to the `workflow` directory in the generated skeleton.
The file name must be `icon.png`

You can assign individual icons to your output items. See the `pyalfred.model.Icon` class for more details.

## Distribution through GitHub releases

The skeleton created by `pyfred new` comes with a GitHub action that creates a draft release whenever a tag starting
with `v` is pushed. To create a tag, run `git tag v1.0.0` and push it with `git push origin v1.0.0`. When the action
has finished, go to the Releases page of your repository and publish the new release.
