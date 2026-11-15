import hashlib
import sqlite3

import pytest

from hive.db import connect, initialize
from hive.repositories import add_repository
from hive.inspector import inspect_repository


def test_inspector_finds_python_symbols(monkeypatch, tmp_path):
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "hive-home"))
    initialize()

    repository_id = add_repository(
        "https://github.com/example/inspector-test"
    )

    project = tmp_path / "project"
    project.mkdir()

    raw_source = (
        b"import os\n"
        b"\n"
        b"class Engine:\n"
        b"    def run(self):\n"
        b"        return True\n"
        b"\n"
        b"def start():\n"
        b"    pass\n"
    )

    source_file = project / "example.py"
    source_file.write_bytes(raw_source)

    result = inspect_repository(repository_id, project)

    assert result["files_inspected"] == 1
    assert result["symbols_found"] >= 4
    assert "Python" in result["languages"]

    symbols = result["files"][0]["symbols"]
    symbol_kinds = {
        symbol["name"]: symbol["kind"]
        for symbol in symbols
    }

    assert {"os", "Engine", "run", "start"} <= set(symbol_kinds)
    assert symbol_kinds["os"] == "import"
    assert symbol_kinds["Engine"] == "class"
    assert symbol_kinds["run"] == "function"
    assert symbol_kinds["start"] == "function"

    assert result["files"][0]["size_bytes"] == len(raw_source)
    assert result["files"][0]["sha256"] == hashlib.sha256(
        raw_source
    ).hexdigest()


def test_inspector_excludes_virtual_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "hive-home"))
    initialize()

    repository_id = add_repository(
        "https://github.com/example/exclusion-test"
    )

    project = tmp_path / "project"
    project.mkdir()

    (project / "main.py").write_text("def main(): pass\n")

    venv = project / ".venv"
    venv.mkdir()
    (venv / "ignored.py").write_text("def ignored(): pass\n")

    result = inspect_repository(repository_id, project)

    assert result["files_inspected"] == 1
    assert result["files"][0]["path"] == "main.py"


def test_inspector_rejects_unknown_repository(monkeypatch, tmp_path):
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "hive-home"))
    initialize()

    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ValueError):
        inspect_repository(999, project)


def test_inspector_removes_stale_file_records(monkeypatch, tmp_path):
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "hive-home"))
    initialize()

    repository_id = add_repository(
        "https://github.com/example/stale-test"
    )

    project = tmp_path / "project"
    project.mkdir()

    source = project / "main.py"
    source.write_text("def active(): pass\n")

    inspect_repository(repository_id, project)

    source.unlink()

    inspect_repository(repository_id, project)

    with connect() as conn:
        files = conn.execute(
            "SELECT COUNT(*) FROM source_files WHERE repository_id=?",
            (repository_id,),
        ).fetchone()[0]

        symbols = conn.execute(
            "SELECT COUNT(*) FROM source_symbols WHERE repository_id=?",
            (repository_id,),
        ).fetchone()[0]

    assert files == 0
    assert symbols == 0


def test_inspector_preserves_previous_snapshot_on_database_failure(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "hive-home"))
    initialize()

    repository_id = add_repository(
        "https://github.com/example/rollback-test"
    )

    project = tmp_path / "project"
    project.mkdir()

    source = project / "main.py"
    source.write_text("def original(): pass\n")

    inspect_repository(repository_id, project)

    with connect() as conn:
        original_file = conn.execute(
            """
            SELECT relative_path, sha256
            FROM source_files
            WHERE repository_id = ?
            """,
            (repository_id,),
        ).fetchone()

        original_symbols = conn.execute(
            """
            SELECT kind, name, line_number
            FROM source_symbols
            WHERE repository_id = ?
            ORDER BY name
            """,
            (repository_id,),
        ).fetchall()

        conn.execute("""
            CREATE TRIGGER force_inspection_failure
            BEFORE INSERT ON source_files
            BEGIN
                SELECT RAISE(ABORT, 'forced test failure');
            END
        """)

    source.write_text("def replacement(): pass\n")

    with pytest.raises(sqlite3.IntegrityError):
        inspect_repository(repository_id, project)

    with connect() as conn:
        current_file = conn.execute(
            """
            SELECT relative_path, sha256
            FROM source_files
            WHERE repository_id = ?
            """,
            (repository_id,),
        ).fetchone()

        current_symbols = conn.execute(
            """
            SELECT kind, name, line_number
            FROM source_symbols
            WHERE repository_id = ?
            ORDER BY name
            """,
            (repository_id,),
        ).fetchall()

    assert tuple(current_file) == tuple(original_file)
    assert [tuple(row) for row in current_symbols] == [
        tuple(row) for row in original_symbols
    ]
