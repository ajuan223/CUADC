import json
import subprocess
from pathlib import Path

from striker.config.field_profile import FieldProfile


def test_exported_sample_passes_field_profile_validation() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tests" / "web" / "generate_field_editor_sample.mjs"
    result = subprocess.run(
        ["node", str(script)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    profile = FieldProfile.model_validate(data)
    assert profile.coordinate_system == "WGS84"
    assert profile.boundary.polygon[0] == profile.boundary.polygon[-1]
