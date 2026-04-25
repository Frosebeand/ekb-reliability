from __future__ import annotations

from ekb_reliability.config import CLASSIFIER_MODEL_PATH, MODEL_DIR, PROJECT_DIR, resolve_classifier_model_path


def test_project_dir_points_to_repo_root():
    assert (PROJECT_DIR / "README.md").exists()
    assert MODEL_DIR == PROJECT_DIR / "models"


def test_classifier_model_path_resolves_to_existing_artifact():
    resolved = resolve_classifier_model_path()
    assert resolved == CLASSIFIER_MODEL_PATH
    assert resolved.exists()
