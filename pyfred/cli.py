import argparse
import logging
import pathlib
import plistlib
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile


def _must_be_run_from_workflow_project_root(
    fn: Callable[[argparse.Namespace], None]
) -> Callable[[argparse.Namespace], None]:
    """Validates that the command is run from a directory that contains a workflow"""

    def decorator(args: argparse.Namespace):
        wf_dir = Path.cwd() / "workflow"
        info_plist_path = wf_dir / "Info.plist"

        if not info_plist_path.exists():
            logging.critical("Cannot find workflow. You need to run this command from the root of the project")
            exit(1)

        fn(args)

    return decorator


def _get_sync_directory() -> Path:
    """
    :return: The path to Alfred's sync directory
    """
    prefs_path = Path.home().joinpath("Library/Preferences/com.runningwithcrayons.Alfred-Preferences.plist")

    if not prefs_path.exists():
        raise ValueError("Alfred doesn't appear to be installed")

    with prefs_path.open("rb") as f:
        pl = plistlib.load(f)

    if "syncfolder" not in pl:
        raise ValueError("Alfred's synchronisation directory not set")

    sync_dir = Path(pl["syncfolder"]).expanduser()

    if not sync_dir.exists():
        raise OSError("Cannot find workflow directory")

    return sync_dir.expanduser()


def _get_workflows_directory() -> Path:
    """
    Get the directory where Alfred stores workflows

    :return: The path to the directory with Alfred's workflows
    """
    return _get_sync_directory() / "Alfred.alfredpreferences" / "workflows"


def _make_plist(
    name: str, keyword: str, bundle_id: str, author: Optional[str], website: Optional[str], description: Optional[str]
) -> dict:
    """
    Create a dictionary representation of the Info.plist file describing the workflow

    :param name:
        The name of the workflow
    :param keyword:
        The keyword to trigger the workflow
    :param bundle_id:
        The bundle ID to identify the workflow. Should use reverse-DNS notation
    :param author:
        The name of the author
    :param website:
        The website of the workflow
    :param description:
        The description of the workflow. Will be shown to the user when importing
    :return: a dictionary representation of the Info.plist file
    """
    script_uuid = str(uuid4())
    clipboard_uuid = str(uuid4())

    return {
        "name": name,
        "description": description or "",
        "bundleid": bundle_id,
        "createdby": author or "",
        "connections": {script_uuid: [{"destinationuid": clipboard_uuid}]},
        "uidata": [],
        # Environment variables
        # Add the vendored directory to the PYTHONPATH so that we're also searching there for dependencies
        "variables": {"PYTHONPATH": ".:vendored"},
        # The workflow version
        "version": "0.0.1",
        # The contact website
        "webaddress": website or "",
        "objects": [
            {"uid": clipboard_uuid, "type": "alfred.workflow.output.clipboard", "config": {"clipboardtext": "{query}"}},
            {
                "uid": script_uuid,
                "type": "alfred.workflow.input.scriptfilter",
                "config": {
                    "keyword": keyword,
                    "scriptfile": "workflow.py",
                    # Keyword should be followed by whitespace
                    "withspace": True,
                    # Argument optional
                    "argumenttype": 1,
                    # Placeholder title
                    "title": "Search",
                    # "Please wait" subtext
                    "runningsubtext": "Loading...",
                    # External script
                    "type": 8,
                    # Terminate previous script
                    "queuemode": 2,
                    # Always run immediately for first typed character
                    "queuedelayimmediatelyinitially": True,
                    # Don't set argv when empty
                    "argumenttreatemptyqueryasnil": True,
                },
            },
        ],
    }


def _zip_dir(directory: Path, output_file: Path):
    """
    Zip the contents of the provided directory recursively

    :param directory: The directory to compress
    :param output_file: The target file
    """

    with ZipFile(output_file, "w", ZIP_DEFLATED) as zip_file:
        for entry in directory.rglob("**/*"):
            if entry.is_file():
                logging.debug("Adding to package: %s", entry)
                zip_file.write(entry, entry.relative_to(directory))
    logging.info("Produced package at %s", output_file)


def find_workflow_link(target: Path) -> Optional[Path]:
    """
    Finds a link to the workflow in Alfred's workflows directory

    :param target: The path to the workflow we're looking for
    :return: The path if found; `None` otherwise
    """
    target = target.expanduser()
    workflows = _get_workflows_directory()

    for wf in workflows.iterdir():
        if wf.is_symlink() and wf.readlink().expanduser() == target:
            return wf

    return None


def new(args: argparse.Namespace):
    """
    Entry point for the `new` command. Creates a new Alfred workflow.

    This creates a directory of the name in the `name` argument and links it into Alfred's workflows directory. The
    workflow shows in the Alfred Preferences app and can still be easily edited with an external editor.

    ```
    usage: pyfred new [-h] -k KEYWORD -b BUNDLE_ID [--author AUTHOR] [--website WEBSITE] [--description DESCRIPTION] [--git | --no-git] name

    positional arguments:
      name                  Name of the new workflow

    options:
      -h, --help            show this help message and exit
      -k KEYWORD, --keyword KEYWORD
                            The keyword to trigger the workflow
      -b BUNDLE_ID, --bundle-id BUNDLE_ID
                            The bundle identifier, usually in reverse DNS notation
      --author AUTHOR       Name of the author
      --website WEBSITE     The workflow website
      --description DESCRIPTION
                            A description for the workflow
      --git, --no-git       Whether to create a git repository (default: True)
    ```
    """  # noqa: E501
    name = args.name
    logging.info("Creating new workflow: %s", name)

    root_dir = Path.cwd().joinpath(name)
    wf_dir = root_dir.joinpath("workflow")

    try:
        logging.debug("Copying template")
        template_dir = Path(pathlib.os.path.dirname(__file__)).joinpath("template")  # type: ignore
        logging.debug("Copying %s to %s", template_dir, root_dir)
        shutil.copytree(template_dir, root_dir)
    except OSError as e:
        logging.error("Cannot create workflow: %s", e)
        exit(1)

    wf_file_path = wf_dir.joinpath("workflow.py")

    logging.debug("Adding +x permission to workflow")
    wf_file_path.chmod(wf_file_path.stat().st_mode | stat.S_IEXEC)

    if args.git:
        logging.debug("Initialising git repository")
        if subprocess.call(["git", "init", args.name]) != 0:
            logging.warning("Failed to create git repository. Ignoring.")

    logging.debug("Creating Info.plist")
    with wf_dir.joinpath("Info.plist").open(mode="wb") as f:
        plistlib.dump(
            _make_plist(
                name=name,
                keyword=args.keyword,
                bundle_id=args.bundle_id,
                author=args.author,
                website=args.website,
                description=args.description,
            ),
            f,
            sort_keys=True,
        )
    _vendor(root_dir)
    _link(relink=True, same_path=False, wf_dir=wf_dir)


@_must_be_run_from_workflow_project_root
def link(args: argparse.Namespace):
    """
    Entry point for the `link` command. Links or relinks the workflow into Alfred's workflows directory.

    ```
    usage: pyfred link [-h] [--relink | --no-relink] [--same-path | --no-same-path]

    options:
      -h, --help            show this help message and exit
      --relink, --no-relink
                            Whether to delete (if exists) and recreate the link (default: False)
      --same-path, --no-same-path
                            Whether to reuse (if exists) the previous path for the link (default: False)
    ```
    """
    try:
        _link(relink=args.relink, same_path=args.same_path, wf_dir=Path.cwd().joinpath("workflow"))
    except ValueError as e:
        logging.error("Error creating link: %s", e)
        exit(1)


def _link(relink: bool, same_path: bool, wf_dir: Path):
    """
    Create a link to the workflow in Alfred's workflows directory

    :param relink:
        Whether to recreate the link if it exists
    :param same_path:
        Whether to reuse the same link if one exists
    :param wf_dir:
        The directory to link to
    :return:
    """
    if not wf_dir.exists():
        raise ValueError(f"{wf_dir} doesn't exist")

    if not wf_dir.is_dir():
        raise ValueError(f"{wf_dir} is not a directory")

    existing_link = find_workflow_link(wf_dir)

    if existing_link:
        if not relink:
            logging.debug("Found link: %s", existing_link)
            return

        logging.debug("Removing existing link: %s", existing_link)
        existing_link.unlink()

    logging.info("Creating link to workflow directory %s", wf_dir)

    if same_path and existing_link:
        source = existing_link
    else:
        workflow_id = str(uuid4()).upper()
        source = _get_workflows_directory().joinpath(f"user.workflow.{workflow_id}")

    logging.debug("Creating link: %s", source)
    source.symlink_to(wf_dir)

    if not source.exists():
        logging.error("Error linking from %s to %s", source, wf_dir)
        source.unlink(missing_ok=True)


@_must_be_run_from_workflow_project_root
def vendor(_args: argparse.Namespace):
    """
    Entry point for the `vendor` command

    Downloads dependencies specified in the `requirements.txt` file into the workflow's `vendored` directory.
    This way, the dependencies don't need to be installed into the system Python interpreter.

    The workflow sets the `PYTHONPATH` environment variable to `.:vendored`, making the interpreter search for
    dependencies in that directory, in addition to the workflow directory.

    ```
    usage: pyfred vendor [-h]

    options:
      -h, --help  show this help message and exit
    ```
    """
    _vendor(root_path=Path.cwd())


def _vendor(root_path: Path) -> bool:
    """
    Download dependencies from `requirements.txt`

    :param root_path: The root path of the workflow project
    :return: whether the download was successful
    """

    vendored_path = root_path / "workflow" / "vendored"
    vendored_path.mkdir(parents=True, exist_ok=True)

    import subprocess

    pip_command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        f"{root_path}/requirements.txt",
        f"--target={vendored_path}",
    ]
    logging.debug("Running pip: python %s", " ".join(pip_command[1:]))

    return subprocess.call(pip_command) == 0


@_must_be_run_from_workflow_project_root
def package(_args: argparse.Namespace):
    """
    Entry point for the `package` command. Creates a package for distribution.

    Packages the workflow into a `workflow.alfredworkflow` file in the `dist` directory.
    Users can import the package by double-clicking the file.

    ```
    usage: pyfred package [-h]

    options:
      -h, --help  show this help message and exit
    ```
    """
    root_dir = Path.cwd()

    if not _vendor(Path.cwd()):
        logging.error("Failed to download dependencies. Exiting")
        exit(1)

    output = root_dir / "dist"
    output.mkdir(exist_ok=True)

    _zip_dir(root_dir / "workflow", output / "workflow.alfredworkflow")


def _cli():
    """
    The entry point for the CLI.

    ```
    usage: pyfred [-h] {new,vendor,link,package} ...

    Build Python workflows for Alfred with ease

    positional arguments:
      {new,vendor,link,package}
        new                 Create a new workflow
        vendor              Install workflow dependencies
        link                Create a symbolic link to this workflow in Alfred
        package             Package the workflow for distribution

    options:
      -h, --help            show this help message and exit
      --debug, --no-debug   Whether to enable debug logging (default: False)
    ```

    """
    parser = argparse.ArgumentParser(prog="pyfred", description="Build Python workflows for Alfred with ease")
    parser.add_argument(
        "--debug", action=argparse.BooleanOptionalAction, default=False, help="Whether to enable debug logging"
    )
    subparsers = parser.add_subparsers(required=True)

    new_parser = subparsers.add_parser("new", help="Create a new workflow")
    new_parser.add_argument("name", type=str, help="Name of the new workflow")
    new_parser.add_argument("-k", "--keyword", type=str, required=True, help="The keyword to trigger the workflow")
    new_parser.add_argument(
        "-b", "--bundle-id", type=str, required=True, help="The bundle identifier, usually in reverse DNS notation"
    )
    new_parser.add_argument("--author", type=str, help="Name of the author")
    new_parser.add_argument("--website", type=str, help="The workflow website")
    new_parser.add_argument("--description", type=str, help="A description for the workflow")
    new_parser.add_argument(
        "--git", action=argparse.BooleanOptionalAction, default=True, help="Whether to create a git repository"
    )
    new_parser.set_defaults(func=new)

    vendor_parser = subparsers.add_parser("vendor", help="Install workflow dependencies")
    vendor_parser.set_defaults(func=vendor)

    link_parser = subparsers.add_parser("link", help="Create a symbolic link to this workflow in Alfred")
    link_parser.add_argument(
        "--relink",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Whether to delete (if exists) and recreate the link",
    )
    link_parser.add_argument(
        "--same-path",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Whether to reuse (if exists) the previous path for the link",
    )
    link_parser.set_defaults(func=link)

    package_parser = subparsers.add_parser("package", help="Package the workflow for distribution")
    package_parser.set_defaults(func=package)

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG if args.debug else logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args.func(args)


if __name__ == "__main__":
    _cli()
