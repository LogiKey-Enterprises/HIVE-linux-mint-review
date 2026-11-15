import ast
import hashlib
import os
from pathlib import Path

from .db import connect


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
}

LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sh": "Shell",
}

MAX_FILE_SIZE = 1_000_000
MAX_FILES = 5000
MAX_TOTAL_BYTES = 25_000_000


def initialize_inspector(path: Path | None = None):
    with connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS source_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                relative_path TEXT NOT NULL,
                language TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                inspected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(repository_id, relative_path),
                FOREIGN KEY(repository_id)
                    REFERENCES repositories(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS source_symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                relative_path TEXT NOT NULL,
                kind TEXT NOT NULL,
                name TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                FOREIGN KEY(repository_id)
                    REFERENCES repositories(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_files_repo
            ON source_files(repository_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_symbols_repo
            ON source_symbols(repository_id)
        """)


def python_symbols(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    symbols = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({
                "kind": "function",
                "name": node.name,
                "line": node.lineno,
            })

        elif isinstance(node, ast.ClassDef):
            symbols.append({
                "kind": "class",
                "name": node.name,
                "line": node.lineno,
            })

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            else:
                names = [node.module or ""]

            for name in names:
                symbols.append({
                    "kind": "import",
                    "name": name,
                    "line": node.lineno,
                })

    return symbols


def inspect_repository(repository_id, root, database_path: Path | None = None):
    root = Path(root).expanduser().resolve()

    if not root.is_dir():
        raise ValueError(f"Repository path is not a directory: {root}")

    initialize_inspector(database_path)

    # Ensure graph storage exists for this database, including explicit paths.
    from .graph import initialize_graph
    initialize_graph(database_path)

    with connect(database_path) as conn:
        repository = conn.execute(
            "SELECT id FROM repositories WHERE id = ?",
            (repository_id,),
        ).fetchone()

    if repository is None:
        raise ValueError(f"Repository ID {repository_id} is not registered")

    results = []
    skipped = 0
    total_bytes = 0

    def raise_walk_error(error):
        raise error

    for current_root, dirs, files in os.walk(
        root,
        followlinks=False,
        onerror=raise_walk_error,
    ):
        current = Path(current_root)

        dirs[:] = [
            name for name in dirs
            if name not in EXCLUDED_DIRS
            and not (current / name).is_symlink()
        ]

        for filename in files:
            path = current / filename

            if path.is_symlink():
                skipped += 1
                continue

            language = LANGUAGES.get(path.suffix.lower())

            if language is None:
                continue

            try:
                estimated_size = path.stat().st_size

                if estimated_size > MAX_FILE_SIZE:
                    skipped += 1
                    continue

                if len(results) >= MAX_FILES:
                    raise ValueError(
                        f"Inspection exceeded the {MAX_FILES} file limit"
                    )

                raw = path.read_bytes()
                size = len(raw)

                if size > MAX_FILE_SIZE:
                    skipped += 1
                    continue

                if total_bytes + size > MAX_TOTAL_BYTES:
                    raise ValueError(
                        "Inspection exceeded the 25 MB total source limit"
                    )

                source = raw.decode("utf-8")

            except UnicodeDecodeError:
                skipped += 1
                continue
            except OSError as exc:
                raise RuntimeError(
                    f"Unable to inspect source file: {path}"
                ) from exc

            relative_path = path.relative_to(root).as_posix()
            digest = hashlib.sha256(raw).hexdigest()

            symbols = (
                python_symbols(source)
                if language == "Python"
                else []
            )

            results.append({
                "path": relative_path,
                "language": language,
                "size_bytes": size,
                "sha256": digest,
                "symbols": symbols,
            })

            total_bytes += size

    # Replace the repository snapshot atomically.
    # A failed database write rolls back and preserves the previous snapshot.
    with connect(database_path) as conn:
        # Inspection changes invalidate the graph snapshot.
        # Keep this deletion in the same transaction as snapshot replacement.
        conn.execute(
            "DELETE FROM source_relationships WHERE repository_id = ?",
            (repository_id,),
        )

        conn.execute(
            "DELETE FROM source_symbols WHERE repository_id = ?",
            (repository_id,),
        )

        conn.execute(
            "DELETE FROM source_files WHERE repository_id = ?",
            (repository_id,),
        )

        for item in results:
            conn.execute("""
                INSERT INTO source_files
                    (repository_id, relative_path, language,
                     size_bytes, sha256)
                VALUES (?, ?, ?, ?, ?)
            """, (
                repository_id,
                item["path"],
                item["language"],
                item["size_bytes"],
                item["sha256"],
            ))

            for symbol in item["symbols"]:
                conn.execute("""
                    INSERT INTO source_symbols
                        (repository_id, relative_path, kind,
                         name, line_number)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    repository_id,
                    item["path"],
                    symbol["kind"],
                    symbol["name"],
                    symbol["line"],
                ))

    return {
        "repository_id": repository_id,
        "root": str(root),
        "files_inspected": len(results),
        "files_skipped": skipped,
        "languages": sorted({
            item["language"] for item in results
        }),
        "symbols_found": sum(
            len(item["symbols"]) for item in results
        ),
        "files": results,
    }
