import json
from pathlib import PosixPath

from pyfred.model import Environment, OutputItem, ScriptFilterOutput
from pyfred.workflow import script_filter


def test_decorator(capsys, monkeypatch):
    monkeypatch.setenv("alfred_preferences", "/Users/Crayons/Dropbox/Alfred/Alfred.alfredpreferences")
    monkeypatch.setenv("alfred_version", "/Users/Crayons/Dropbox/Alfred/Alfred.alfredpreferences")
    monkeypatch.setenv("alfred_preferences", "/Users/Crayons/Dropbox/Alfred/Alfred.alfredpreferences")
    monkeypatch.setenv("alfred_preferences_localhash", "adbd4f66bc3ae8493832af61a41ee609b20d8705")
    monkeypatch.setenv("alfred_theme", "alfred.theme.yosemite")
    monkeypatch.setenv("alfred_theme_background", "rgba(255,255,255,0.98)")
    monkeypatch.setenv("alfred_theme_subtext", "3")
    monkeypatch.setenv("alfred_version", "5.0")
    monkeypatch.setenv("alfred_version_build", "2058")
    monkeypatch.setenv("alfred_workflow_bundleid", "com.alfredapp.googlesuggest")
    monkeypatch.setenv(
        "alfred_workflow_cache",
        "/Users/Crayons/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/com.alfredapp.googlesuggest",
    )
    monkeypatch.setenv(
        "alfred_workflow_data",
        "/Users/Crayons/Library/Application Support/Alfred/Workflow Data/com.alfredapp.googlesuggest",
    )
    monkeypatch.setenv("alfred_workflow_name", "Google Suggest")
    monkeypatch.setenv("alfred_workflow_version", "1.7")
    monkeypatch.setenv("alfred_workflow_uid", "user.workflow.B0AC54EC-601C-479A-9428-01F9FD732959")
    monkeypatch.setenv("alfred_debug", "1")

    @script_filter
    def under_test(path, args, env):
        assert path.exists()
        assert isinstance(args, list)
        assert env == Environment(
            debug=True,
            preferences_file=PosixPath("/Users/Crayons/Dropbox/Alfred/Alfred.alfredpreferences"),
            version="5.0",
            version_build="2058",
            workflow_name="Google Suggest",
            workflow_version="1.7",
            workflow_bundle_id=None,
            workflow_uid="user.workflow.B0AC54EC-601C-479A-9428-01F9FD732959",
            workflow_cache=PosixPath(
                "/Users/Crayons/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/com.alfredapp.googlesuggest"
            ),
            workflow_data=PosixPath(
                "/Users/Crayons/Library/Application Support/Alfred/Workflow Data/com.alfredapp.googlesuggest"
            ),
        )
        return ScriptFilterOutput(items=[OutputItem(title="Hello Alfred!")])

    under_test()

    output = json.loads(capsys.readouterr().out)

    assert output == {"items": [{"title": "Hello Alfred!", "type": "default"}]}
