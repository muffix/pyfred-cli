import pytest

from pyfred.model import Icon, OutputItem, ScriptFilterOutput


def test_model_validation():
    with pytest.raises(ValueError):
        OutputItem(title="")

    with pytest.raises(ValueError):
        ScriptFilterOutput(rerun=10)

    with pytest.raises(ValueError):
        Icon(type="invalid", path="public.jpeg")
