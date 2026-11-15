import pytest
from hive.db import initialize
from hive.repositories import add_repository, list_repositories, normalize_github_url
from hive.capabilities import add_capability, list_capabilities

def test_repository_url_normalization():
    assert normalize_github_url("https://github.com/tree-sitter/tree-sitter.git")==("tree-sitter","tree-sitter")
    with pytest.raises(ValueError): normalize_github_url("https://example.com/project")

def test_repository_upsert_and_capability(monkeypatch,tmp_path):
    monkeypatch.setenv("HIVE_HOME",str(tmp_path/"hive-home")); initialize()
    rid=add_repository("https://github.com/example/project",language="Python",stars=12)
    assert rid==add_repository("https://github.com/example/project",description="Example")
    assert len(list_repositories())==1
    cid=add_capability(rid,"API integration",evidence_level="claimed",evidence="Documented in README")
    assert cid>0 and len(list_capabilities())==1

def test_invalid_evidence_level(monkeypatch,tmp_path):
    monkeypatch.setenv("HIVE_HOME",str(tmp_path/"hive-home")); initialize()
    rid=add_repository("https://github.com/example/another")
    with pytest.raises(ValueError): add_capability(rid,"something",evidence_level="proven")
