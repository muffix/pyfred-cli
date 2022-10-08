import logging
import os
import plistlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union, cast


class Key(Enum):
    """
    Modifier keys that can be used to modify `OutputItems`
    """

    Cmd = "cmd"
    Option = "alt"
    Control = "ctrl"
    Shift = "shift"
    Fn = "fn"


@dataclass(frozen=True)
class Icon:
    """
    Icon for `OutputItem`s

    If unset, defaults to the workflow icon.
    """

    path: str = ""
    """
    A resource to load an item from.

    Can be a path to an image file (if `type` unset), a path to a file whose icon is to be used (if `type` is
    `fileicon`, or a UTI (if `type` is `filetype`).
    """
    type: Optional[str] = None
    """The type of resource that `path` specifies. Must be one of ``, `fileicon`, `filetype`."""

    @classmethod
    def image(cls, path: str) -> "Icon":
        """
        Get an icon with the contents of the image at `path`

        :return: an `Icon` that can be used in `OutputItem`
        """
        return Icon(path)

    @classmethod
    def file_icon(cls, path: str) -> "Icon":
        """
        Get an icon with the same icon as the file at `path`

        For example, to get a calendar icon, specify the path of the macOS built-in Calendar app:

        ```python
        Icon.file_icon(path="/System/Applications/Calendar.app")
        ```

        :return: an `Icon` that can be used in `OutputItem`
        """
        return Icon(path, type="fileicon")

    @classmethod
    def uti(cls, uti: str) -> "Icon":
        """
        Get an icon with the same icon as the file at `path`

        macOS comes with built-in icons for many types of data, declared as Uniform Type Identifiers (UTIs).
        We can tell Alfred to use these icons by just specifying the UTI.

        An outdated list of available UTIs can be found on the [Apple website](https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/UTIRef/Articles/System-DeclaredUniformTypeIdentifiers.html#//apple_ref/doc/uid/TP40009259-SW1).

        It's possible to dump the available UTIs on a system using the following command:
        ```sh
        /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -dump | grep uti: | cut -c 29- | sort | uniq
        ```

        To use the macOS icon for a JPEG image:
        ```python
        Icon.uti(uti="public.jpeg")
        ```

        :return: an `Icon` that can be used in `OutputItem`
        """  # noqa: E501
        return Icon(uti, type="filetype")

    def __post_init__(self):
        if self.type and self.type not in ("fileicon", "filetype"):
            raise ValueError("if set, type must be either fileicon or filetype")


class Type(Enum):
    """
    The type of output

    By specifying `File`, Alfred treats your result as a file on your system. This allows the user to perform actions on
    the file like they can with Alfred's standard file filters.

    When returning files, Alfred will check if they exist before presenting that result to the user. This has a very
    small performance implication but makes results as predictable as possible. If you would like Alfred to skip this
    check because you are certain the files you are returning exist, use `FileSkipCheck`.
    """

    Default = "default"
    File = "file"
    FileSkipCheck = "file:skipcheck"


@dataclass(frozen=True)
class Text:
    """
    Defines the text the user will get when copying the selected result row with ⌘C or displaying large type with ⌘L
    """

    copy: Optional[str] = None
    """The text to copy"""
    large_type: Optional[str] = None
    """The text to display"""

    def __post_init__(self):
        if self.copy is None and self.large_type is None:
            raise ValueError("At least one of copy or large_type must be set")


@dataclass(frozen=True)
class Data:
    """The new values to override parts of an OutputItem"""

    subtitle: Optional[str] = None
    """Second line of the item"""
    arg: Optional[str] = None
    """The value to be passed to the next input"""
    icon: Optional[Icon] = None
    """An icon to display next to the item. Defaults to the workflow icon if not set"""
    valid: Optional[bool] = None
    """Whether the item is selectable"""


@dataclass(frozen=True)
class Action:
    """
    Script filter result that is passed to Universal Actions if its item is selected

    This allows to assert the type of the values passed to Universal Actions. More than one item can be returned here so
    that the action selected in the next step is performed on all of them.

    See [Universal Actions](https://www.alfredapp.com/help/features/universal-actions/) for details.
    """

    text: Optional[Union[str, list[str]]]
    """The value to be passed to Universal actions as text"""
    url: Optional[Union[str, list[str]]]
    """The value to be passed to Universal actions as URL"""
    file: Optional[Union[str, list[str]]]
    """The path to a file to be passed to Universal actions as text"""
    auto: Optional[Union[str, list[str]]]
    """The value to be passed to Universal actions for it to autodetect the type"""


@dataclass(frozen=True)
class OutputItem:
    """An item to be displayed for selection in Alfred"""

    title: str
    """First line of the item"""
    subtitle: Optional[str] = None
    """Second line of the item"""
    uid: Optional[str] = None
    """A UID to allow Alfred to identify a response and determine frequently used ones"""
    arg: Optional[str] = None
    """The value to be passed to the next input"""
    icon: Optional[Icon] = None
    """An icon to display next to the item. Defaults to the workflow icon if not set"""
    valid: Optional[bool] = None
    """Whether the item is selectable"""
    match: Optional[str] = None
    """String to use for Alfred to match if workflow set to "Alfred Filters Results". Uses title if not set"""
    autocomplete: Optional[str] = None
    """String to be filled into the Alfred bar when the user presses autocomplete"""
    mods: Optional[dict[Union[Key, str], Data]] = None
    """Mapping of modifier key to values to be overridden for this item if the user presses the respective key"""
    text: Optional[Text] = None
    """
    Defines the text the user will get when copying the selected result row with ⌘C or displaying large type with ⌘L
    """
    quicklook_url: Optional[str] = None
    """
    A Quick Look URL which will be visible if the user uses the Quick Look feature within Alfred.

    Accepts URLs and file paths.
    """
    actions: Optional[Union[str, list[str], Action]] = None
    """
    Items to be passed to Universal Actions if this item is selected. Overrides `args` if set.

    This can either be a single string, a list of strings or an `Action` instance. If it's not an `Action` instance,
    Universal Actions will try to determine the type of the value (file, URL, or text).

    If set, the next input in the workflow should be "Universal Action".
    """
    type: Union[Type, str] = Type.Default
    """The type of `arg`"""

    def __post_init__(self):
        if not self.type:
            object.__setattr__(self, "type", Type.Default)

        if isinstance(self.type, Type):
            object.__setattr__(self, "type", self.type.value)

        if self.mods is not None:
            object.__setattr__(self, "mods", {k.value: v for k, v in self.mods.items()})

        if not self.title:
            raise ValueError("title must be set")


@dataclass(frozen=True)
class ScriptFilterOutput:
    """The class to be returned by the script filter entrypoint"""

    rerun: Optional[int] = None
    """Time in seconds in which to run the script filter again. Must be between 0.1 and 5 seconds"""
    items: Optional[list[OutputItem]] = None
    """The items to be displayed for selection in Alfred"""
    variables: Optional[dict[str, str]] = None
    """
    The variables to pass to the next input

    The variables are also available to reruns of this filter. This is useful to keep state between runs.
    """

    def __post_init__(self):
        if self.rerun is not None and not 0.1 <= self.rerun <= 5:
            raise ValueError("rerun must be between 0.1 and 5")


@dataclass(frozen=True)
class Environment:
    """
    The environment variables passed by Alfred

    See [here](https://www.alfredapp.com/help/workflows/script-environment-variables/) for more details.
    """

    debug: bool
    """Whether Alfred is running in debug mode"""
    preferences_file: Path
    """The path to Alfred's preferences file"""
    version: str
    """The Alfred version (e.g., `v5.0.0`)"""
    version_build: str
    """The Alfred build (e.g., `1234`)"""
    workflow_name: str
    """The name of the workflow being executed"""
    workflow_version: Optional[str]
    """The version of the workflow"""
    workflow_bundle_id: Optional[str]
    """The bundle ID of the workflow, if set"""
    workflow_uid: str
    """The UID of the workflow"""
    workflow_cache: Optional[Path]
    """The path to the workflow's cache directory"""
    workflow_data: Optional[Path]
    """The path to the workflow's data directory"""

    @classmethod
    def from_env(cls) -> Optional["Environment"]:
        """
        Get Alfred's environment variables

        :return: a model populated from the environment variables set by Alfred
        """

        if not os.environ.get("alfred_version"):
            logging.warning("Not running in an Alfred environment")
            return None

        cache_dir = os.environ.get("alfred_workflow_cache")
        data_dir = os.environ.get("alfred_workflow_data")
        cast(str, os.environ.get("alfred_preferences"))

        return Environment(
            debug=(os.environ.get("alfred_debug") == "1"),
            preferences_file=Path(cast(str, os.environ.get("alfred_preferences"))),
            version=cast(str, os.environ.get("alfred_version")),
            version_build=cast(str, os.environ.get("alfred_version_build")),
            workflow_name=cast(str, os.environ.get("alfred_workflow_name")),
            workflow_version=os.environ.get("alfred_workflow_version"),
            workflow_bundle_id=os.environ.get("alfred_workflow_bundle_id"),
            workflow_uid=os.environ.get("alfred_workflow_uid") or "",
            workflow_cache=Path(cache_dir).expanduser() if cache_dir else None,
            workflow_data=Path(data_dir).expanduser() if data_dir else None,
        )

    @property
    def preferences(self) -> dict:
        """
        Get Alfred's preferences

        :return: a dictionary representation of the Alfred preferences file
        """
        with self.preferences_file.open("rb") as f:
            prefs = plistlib.load(f)
        return prefs
