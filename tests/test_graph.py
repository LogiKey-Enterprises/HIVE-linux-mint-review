import sqlite3

import pytest

from hive.db import connect, initialize
from hive.repositories import add_repository
from hive.inspector import inspect_repository
from hive.graph import build_graph, show_graph


def setup_project(monkeypatch, tmp_path, files):
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "hive-home"))
    initialize()

    repository_id = add_repository(
        "https://github.com/example/graph-test"
    )

    project = tmp_path / "project"
    project.mkdir()

    for relative_path, source in files.items():
        path = project / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)

    inspect_repository(repository_id, project)

    return repository_id, project


def test_graph_resolves_direct_imports(monkeypatch, tmp_path):
    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "from hive_module import run\n",
            "hive_module.py": "def run():\n    pass\n",
        },
    )

    result = build_graph(repository_id, project)

    assert result["files_considered"] == 2
    assert result["relationships_found"] == 1

    relationship = result["relationships"][0]

    assert relationship["source_path"] == "main.py"
    assert relationship["target_path"] == "hive_module.py"
    assert relationship["imported_name"] == "hive_module.run"


def test_graph_resolves_relative_package_imports(
    monkeypatch, tmp_path
):
    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/module.py": "from . import sibling\n",
            "pkg/sibling.py": "VALUE = 1\n",
        },
    )

    result = build_graph(repository_id, project)

    assert result["relationships_found"] == 1

    relationship = result["relationships"][0]

    assert relationship["source_path"] == "pkg/module.py"
    assert relationship["target_path"] == "pkg/sibling.py"
    assert relationship["imported_name"] == "pkg.sibling"


def test_graph_rebuild_is_repeatable(monkeypatch, tmp_path):
    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import helper\n",
            "helper.py": "VALUE = 1\n",
        },
    )

    first = build_graph(repository_id, project)
    first_rows = show_graph(repository_id)

    second = build_graph(repository_id, project)
    second_rows = show_graph(repository_id)

    assert first["relationships_found"] == 1
    assert second["relationships_found"] == 1
    assert first_rows == second_rows


def test_graph_preserves_previous_snapshot_on_database_failure(
    monkeypatch, tmp_path
):
    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import original\n",
            "original.py": "VALUE = 1\n",
            "replacement.py": "VALUE = 2\n",
        },
    )

    build_graph(repository_id, project)
    original_rows = show_graph(repository_id)

    with connect() as conn:
        conn.execute("""
            CREATE TRIGGER force_graph_failure
            BEFORE INSERT ON source_relationships
            BEGIN
                SELECT RAISE(ABORT, 'forced graph failure');
            END
        """)

    with pytest.raises(sqlite3.IntegrityError):
        build_graph(repository_id, project)

    assert show_graph(repository_id) == original_rows


def test_graph_dependencies_and_dependents(monkeypatch, tmp_path):
    from hive.graph import dependencies_for_file, dependents_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import helper\n",
            "helper.py": "VALUE = 1\n",
            "consumer.py": "import main\n",
        },
    )

    build_graph(repository_id, project)

    dependencies = dependencies_for_file(repository_id, "main.py")
    dependents = dependents_for_file(repository_id, "main.py")

    assert len(dependencies) == 1
    assert dependencies[0]["source_path"] == "main.py"
    assert dependencies[0]["target_path"] == "helper.py"

    assert len(dependents) == 1
    assert dependents[0]["source_path"] == "consumer.py"
    assert dependents[0]["target_path"] == "main.py"


def test_graph_traversal_rejects_unknown_repository(
    monkeypatch, tmp_path
):
    from hive.graph import dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {"main.py": "VALUE = 1\n"},
    )

    with pytest.raises(ValueError, match="not registered"):
        dependencies_for_file(99999, "main.py")


def test_graph_traversal_rejects_uninspected_file(
    monkeypatch, tmp_path
):
    from hive.graph import dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {"main.py": "VALUE = 1\n"},
    )

    with pytest.raises(ValueError, match="not registered as inspected"):
        dependencies_for_file(repository_id, "missing.py")


def test_recursive_dependencies_follow_multiple_levels(
    monkeypatch, tmp_path
):
    from hive.graph import recursive_dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import service\n",
            "service.py": "import database\n",
            "database.py": "import config\n",
            "config.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    results = recursive_dependencies_for_file(
        repository_id, "main.py"
    )

    depths = {
        row["target_path"]: row["depth"]
        for row in results
    }

    assert depths == {
        "service.py": 1,
        "database.py": 2,
        "config.py": 3,
    }


def test_recursive_dependents_follow_multiple_levels(
    monkeypatch, tmp_path
):
    from hive.graph import recursive_dependents_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import service\n",
            "service.py": "import database\n",
            "database.py": "import config\n",
            "config.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    results = recursive_dependents_for_file(
        repository_id, "config.py"
    )

    depths = {
        row["source_path"]: row["depth"]
        for row in results
    }

    assert depths == {
        "database.py": 1,
        "service.py": 2,
        "main.py": 3,
    }


def test_recursive_dependencies_respect_max_depth(
    monkeypatch, tmp_path
):
    from hive.graph import recursive_dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import service\n",
            "service.py": "import database\n",
            "database.py": "import config\n",
            "config.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    results = recursive_dependencies_for_file(
        repository_id, "main.py", max_depth=2
    )

    assert {row["target_path"] for row in results} == {
        "service.py",
        "database.py",
    }


def test_circular_dependency_groups_detect_three_file_cycle(
    monkeypatch, tmp_path
):
    from hive.graph import circular_dependency_groups

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "alpha.py": "import beta\n",
            "beta.py": "import gamma\n",
            "gamma.py": "import alpha\n",
        },
    )

    build_graph(repository_id, project)

    groups = circular_dependency_groups(repository_id)

    assert len(groups) == 1
    assert groups[0]["files"] == [
        "alpha.py",
        "beta.py",
        "gamma.py",
    ]
    assert len(groups[0]["relationships"]) == 3


def test_circular_dependency_detection_ignores_acyclic_files(
    monkeypatch, tmp_path
):
    from hive.graph import circular_dependency_groups

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "alpha.py": "import beta\n",
            "beta.py": "import alpha\n",
            "main.py": "import helper\n",
            "helper.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    groups = circular_dependency_groups(repository_id)

    assert len(groups) == 1
    assert groups[0]["files"] == ["alpha.py", "beta.py"]


def test_recursive_dependencies_handle_diamond_graph(
    monkeypatch, tmp_path
):
    from hive.graph import recursive_dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import left\nimport right\n",
            "left.py": "import shared\n",
            "right.py": "import shared\n",
            "shared.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    results = recursive_dependencies_for_file(
        repository_id, "main.py"
    )

    depths = {
        row["target_path"]: row["depth"]
        for row in results
    }

    assert depths == {
        "left.py": 1,
        "right.py": 1,
        "shared.py": 2,
    }


def test_recursive_dependencies_terminate_on_cycle(
    monkeypatch, tmp_path
):
    from hive.graph import recursive_dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "alpha.py": "import beta\n",
            "beta.py": "import alpha\nimport gamma\n",
            "gamma.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    results = recursive_dependencies_for_file(
        repository_id, "alpha.py"
    )

    depths = {
        row["target_path"]: row["depth"]
        for row in results
    }

    assert depths == {
        "beta.py": 1,
        "gamma.py": 2,
    }


def test_recursive_dependents_handle_converging_paths(
    monkeypatch, tmp_path
):
    from hive.graph import recursive_dependents_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import left\nimport right\n",
            "left.py": "import shared\n",
            "right.py": "import shared\n",
            "shared.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    results = recursive_dependents_for_file(
        repository_id, "shared.py"
    )

    depths = {
        row["source_path"]: row["depth"]
        for row in results
    }

    assert depths == {
        "left.py": 1,
        "right.py": 1,
        "main.py": 2,
    }


def test_recursive_traversal_rejects_invalid_max_depth(
    monkeypatch, tmp_path
):
    import pytest
    from hive.graph import recursive_dependencies_for_file

    repository_id, project = setup_project(
        monkeypatch,
        tmp_path,
        {
            "main.py": "import helper\n",
            "helper.py": "VALUE = 1\n",
        },
    )

    build_graph(repository_id, project)

    for invalid_depth in (0, -1, 1.5, True, "2"):
        with pytest.raises(ValueError):
            recursive_dependencies_for_file(
                repository_id,
                "main.py",
                max_depth=invalid_depth,
            )




def test_explicit_database_paths_are_isolated(monkeypatch, tmp_path):
    from hive.graph import (
        circular_dependency_groups,
        dependencies_for_file,
        recursive_dependencies_for_file,
    )

    # Create a separate default database to detect accidental fallback.
    monkeypatch.setenv("HIVE_HOME", str(tmp_path / "default-home"))
    default_db = initialize()

    db_a = tmp_path / "database_a.sqlite"
    db_b = tmp_path / "database_b.sqlite"

    initialize(db_a)
    initialize(db_b)

    # Insert the same repository ID into both independent databases.
    def insert_repository(database, name):
        with connect(database) as conn:
            conn.execute(
                """
                INSERT INTO repositories (owner, name, url)
                VALUES (?, ?, ?)
                """,
                (
                    "example",
                    name,
                    f"https://github.com/example/{name}",
                ),
            )
            return conn.execute(
                "SELECT id FROM repositories WHERE name = ?",
                (name,),
            ).fetchone()["id"]

    repository_a = insert_repository(db_a, "project-a")
    repository_b = insert_repository(db_b, "project-b")

    assert repository_a == repository_b == 1

    # Database A contains a circular dependency.
    project_a = tmp_path / "project_a"
    project_a.mkdir()
    (project_a / "main.py").write_text("import alpha\n")
    (project_a / "alpha.py").write_text("import main\n")

    # Database B contains a different, acyclic dependency.
    project_b = tmp_path / "project_b"
    project_b.mkdir()
    (project_b / "main.py").write_text("import beta\n")
    (project_b / "beta.py").write_text("VALUE = 1\n")

    inspect_repository(repository_a, project_a, db_a)
    inspect_repository(repository_b, project_b, db_b)

    graph_a = build_graph(repository_a, project_a, db_a)
    graph_b = build_graph(repository_b, project_b, db_b)

    assert graph_a["relationships_found"] == 2
    assert graph_b["relationships_found"] == 1

    # Verify direct graph queries use the selected database.
    dependencies_a = dependencies_for_file(
        repository_a, "main.py", db_a
    )
    dependencies_b = dependencies_for_file(
        repository_b, "main.py", db_b
    )

    assert [row["target_path"] for row in dependencies_a] == [
        "alpha.py"
    ]
    assert [row["target_path"] for row in dependencies_b] == [
        "beta.py"
    ]

    # Verify recursive traversal also uses the selected database.
    recursive_a = recursive_dependencies_for_file(
        repository_a, "main.py", path=db_a
    )
    recursive_b = recursive_dependencies_for_file(
        repository_b, "main.py", path=db_b
    )

    assert {row["target_path"] for row in recursive_a} == {
        "alpha.py"
    }
    assert {row["target_path"] for row in recursive_b} == {
        "beta.py"
    }

    # Verify cycle detection is isolated.
    cycles_a = circular_dependency_groups(repository_a, db_a)
    cycles_b = circular_dependency_groups(repository_b, db_b)

    assert len(cycles_a) == 1
    assert cycles_a[0]["files"] == ["alpha.py", "main.py"]
    assert cycles_b == []

    # Verify the default database was not modified.
    with connect(default_db) as conn:
        default_repositories = conn.execute(
            "SELECT COUNT(*) FROM repositories"
        ).fetchone()[0]

        default_files = conn.execute(
            "SELECT COUNT(*) FROM source_files"
        ).fetchone()[0]

        default_relationships = conn.execute(
            "SELECT COUNT(*) FROM source_relationships"
        ).fetchone()[0]

    assert default_repositories == 0
    assert default_files == 0
    assert default_relationships == 0
