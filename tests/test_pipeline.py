import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")

from app.pipeline import run_pipeline  # noqa: E402


def test_pipeline_runs_end_to_end_in_mock_mode():
    result = run_pipeline("shishper_lake", run_date="2026-08-27")
    assert result["region_id"] == "shishper_lake"
    assert "risk_score" in result["risk"]
    assert os.path.exists(result["image_path"])
    # alerts key always present, populated only if risk crossed threshold
    assert "alerts" in result


def test_unknown_region_raises():
    import pytest

    with pytest.raises(KeyError):
        run_pipeline("not_a_real_region")
