#!/usr/bin/env python3

import logging
from pathlib import Path
from typing import Optional

from vendored.pyfred.model import Environment, OutputItem, ScriptFilterOutput
from vendored.pyfred.workflow import script_filter


@script_filter
def main(script_path: Path, args_from_alfred: list[str], env: Optional[Environment]) -> ScriptFilterOutput:
    """Entrypoint for the workflow"""

    logging.debug("Running workflow script: %s", script_path)
    logging.debug("Arguments: %s", args_from_alfred)
    logging.debug("Alfred environment: %s", env)

    return ScriptFilterOutput(items=[OutputItem(title="Hello Alfred!", arg="Hello Alfred!")])


if __name__ == "__main__":
    main()
