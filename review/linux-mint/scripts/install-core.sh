#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "\nSTOPPED at line %s; retain output and partial directory.\n" "$LINENO" >&2' ERR
umask 077
for tool in git python3; do command -v "$tool" >/dev/null; done
python3 -c 'import sys, venv, ensurepip, sqlite3, ssl; assert sys.version_info >= (3,10)'
# If prerequisites are absent on Mint: git python3-venv python3-pip.
hive_dir="$(mktemp -d "$HOME/HIVE-mint-review-XXXXXXXX")"
pin="4d00a485120607f70b078301dfb8f008ad14ba53"
printf 'Installation directory: %s\n' "$hive_dir"
git clone https://github.com/bargeranthony-gif/HIVE.git "$hive_dir"
cd "$hive_dir"
git checkout --detach "$pin"
test "$(git rev-parse HEAD)" = "$pin"
git rev-parse HEAD > INSTALL_COMMIT.txt
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pip check
export HIVE_HOME="$hive_dir/local-state"
python -m pytest -q tests | tee INSTALL_TEST_RESULTS.txt
hive init
repo_id="$(python -c 'from hive.repositories import add_repository; print(add_repository("https://github.com/bargeranthony-gif/HIVE"))')"
hive inspect "$repo_id" "$hive_dir"
hive graph build "$repo_id" "$hive_dir"
hive graph dependencies "$repo_id" hive/cli.py
hive status
printf '\nCore reproduction complete. For subsequent scripts:\n'
printf 'export HIVE_INSTALL_DIR=%q\n' "$hive_dir"
printf 'export HIVE_HOME=%q\n' "$HIVE_HOME"
printf 'source %q\n' "$hive_dir/.venv/bin/activate"
