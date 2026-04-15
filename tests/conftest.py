import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api as api_module
from src.infrastructure.storage import SQLiteStorage


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_storage = SQLiteStorage(str(tmp_path / "test.db"))
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(api_module, "storage", test_storage)
    monkeypatch.setattr(api_module, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(api_module, "fetch_all_jobs", lambda: [
        SimpleNamespace(title="Backend Engineer", company="ACME", score=91, ai_score=77, source="test", url="https://jobs.example/1"),
        SimpleNamespace(title="Frontend Engineer", company="ACME", score=88, ai_score=73, source="test", url="https://jobs.example/2"),
    ])
    monkeypatch.setattr(api_module, "rank_jobs", lambda jobs: jobs)
    monkeypatch.setattr(api_module, "calculate_ai_scores", lambda resume_text, ranked: ranked)
    monkeypatch.setattr(api_module, "extract_text_from_pdf", lambda path: "python react fastapi")
    monkeypatch.setattr(api_module, "determine_career_info", lambda text: {"focus": "Engineering", "skills": {}})

    return TestClient(api_module.app)
