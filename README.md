# HIVE Engine v0.1

A lightweight foundation for HIVE: configuration, a SQLite knowledge registry,
GitHub repository discovery, capability records, and evidence tracking.

## Design constraints
- Python 3.10+
- Standard library at runtime; no AI model or database server required
- SQLite database stored locally
- Network access is used only when `hive discover` is explicitly run
- GitHub token is optional; set `GITHUB_TOKEN` to improve API rate limits

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
hive init
hive status
pytest
```

## Commands
```bash
hive init
hive status
hive repo add https://github.com/owner/project
hive repo list
hive discover "tree-sitter language parser"
hive capability add <repo_id> "source parsing" --evidence "README states parser support"
hive capability list
```

Discovery is opt-in. It searches GitHub's public repository API and stores basic
metadata; it does not clone or execute downloaded code.

## Evidence discipline
- `claimed`: stated by a project or its documentation
- `inferred`: inferred from metadata or static inspection
- `build_verified`: a build completed in a controlled environment
- `test_verified`: relevant automated tests passed
- `benchmarked`: performance was measured under recorded conditions

HIVE must not promote a claim to a verified level without recorded evidence.

## Data location
Default: `~/.hive/hive.db`. Set `HIVE_HOME` to move HIVE state, for example:
`export HIVE_HOME="/path/to/external-ssd/HIVE"`

## Current limitations
This is a foundation, not yet a source-code analyzer or agent runtime.
No repository is cloned, parsed, built, sandboxed, or executed in this version.
