import argparse
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from pyfred.cli import _get_workflows_directory, link, new, package, vendor
from pyfred.model import Data, Icon, Key, OutputItem, ScriptFilterOutput, Text, Type


def test_new(tmpdir):
    tmpdir = Path(tmpdir)
    sync_dir = tmpdir / "sync"
    workflows = sync_dir / "Alfred.alfredpreferences/workflows"
    workflows.mkdir(parents=True)

    args = MagicMock(
        sprc=argparse.Namespace,
        keyword="test",
        bundle_id="com.example.test",
        author=None,
        website=None,
        description=None,
    )
    args.name = "test_wf"

    expected_git_call = call(["git", "init", "test_wf"])
    expected_vendor_call = call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            f"{tmpdir/'test_wf'/'requirements.txt'}",
            f"--target={tmpdir/'test_wf'/'workflow'/'vendored'}",
        ]
    )

    with patch("pathlib.Path.cwd", return_value=tmpdir):
        with patch("pyfred.cli._get_sync_directory", return_value=sync_dir):
            with patch("subprocess.call", return_value=0) as mock_sub:
                new(args)
                assert mock_sub.call_count == 2
                mock_sub.assert_has_calls([expected_git_call, expected_vendor_call])

    assert (tmpdir / "test_wf/workflow/workflow.py").exists()
    installed_workflows = list(workflows.iterdir())
    assert len(installed_workflows) == 1
    assert installed_workflows[0].is_symlink()
    assert installed_workflows[0].readlink() == tmpdir / "test_wf" / "workflow"


def test_get_workflows_directory():
    expected = Path.home() / "Library/Application Support/Alfred/Alfred.alfredpreferences/workflows"

    with patch("pyfred.cli._get_sync_directory", return_value=None):
        assert _get_workflows_directory() == expected


def test_full_model_serialises_to_json():
    output = ScriptFilterOutput(
        rerun=4.2,
        items=[
            OutputItem(
                title="Hello Alfred!",
                subtitle="a string",
                uid="fake_uid",
                icon=Icon.uti("public.jpeg"),
                valid=True,
                match="Hi",
                autocomplete="Hello Alfred!",
                mods={
                    Key.Cmd: Data(
                        subtitle="My new subtitle",
                        arg="An overridden argument",
                        icon=Icon.file_icon("/System/Applications/Calendar.app"),
                        valid=True,
                    )
                },
                text=Text(large_type="Large type this", copy="Copy that"),
                quicklook_url="https://example.com",
                type=Type.Default,
            ),
            OutputItem(title="A minimal item"),
        ],
        variables={"key": 42},
    )

    assert json.dumps(output, default=vars)


def test_exits_if_not_in_workflow_dir(tmpdir):
    with patch("pathlib.Path.cwd", return_value=tmpdir):
        for func in (link, package, vendor):
            with pytest.raises(SystemExit) as excinfo:
                func(MagicMock(spec=argparse.Namespace))
            assert excinfo.value.code == 1
