import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from pyfred.model import Environment, ScriptFilterOutput


def script_filter(fn: Callable[[Path, list[str], Optional[Environment]], ScriptFilterOutput]):
    """
    Decorator for a script filter

    Preprocesses the input and parses environment variables. The main function of the filter should be decorated with
    this.
    """

    path, args = (sys.argv[0], sys.argv[1:])
    alfred_environment = Environment.from_env()

    is_debug = alfred_environment is None or alfred_environment.debug

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG if is_debug else logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def vars_if_set(obj: Any) -> dict:
        return {k: v for k, v in vars(obj).items() if v is not None}

    def decorator():
        output = fn(Path(path), args, alfred_environment)

        if not isinstance(output, ScriptFilterOutput):
            logging.error(
                "The workflow returned an unexpected type: %s, but expected %s.%s.",
                type(output),
                ScriptFilterOutput.__module__,
                ScriptFilterOutput.__name__,
            )
            logging.debug("Unexpected instance of type %s: %s", type(output), repr(output))
            exit(1)

        print(json.dumps(output, default=vars_if_set))

    return decorator
