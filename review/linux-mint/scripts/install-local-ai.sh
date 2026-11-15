#!/usr/bin/env bash
# Downloads only; does not start the server.
set -Eeuo pipefail
trap 'printf "\nSTOPPED at line %s; retain files for diagnosis.\n" "$LINENO" >&2' ERR
umask 077
test "$(uname -m)" = x86_64
for tool in curl tar sha256sum python3; do command -v "$tool" >/dev/null; done
ai_dir="${HIVE_AI_DIR:-$HOME/.local/share/hive-local-ai-b12110}"
test ! -e "$ai_dir" || { printf 'STOP: %s exists; nothing overwritten.\n' "$ai_dir"; exit 1; }
python3 - "$HOME" <<'PY'
import shutil, sys
assert shutil.disk_usage(sys.argv[1]).free >= 3 * 1024**3, "At least 3 GiB free required"
PY
mkdir -p "$ai_dir/runtime"
cd "$ai_dir"
curl --fail --location --retry 2 -o runtime.tar.gz \
  https://github.com/ggml-org/llama.cpp/releases/download/b12110/llama-b12110-bin-ubuntu-x64.tar.gz
printf '%s  runtime.tar.gz\n' \
  368227edcc229be5f9bed16a2223d79b5e41d0ac2e19bcf5825e82291c060e55 | sha256sum --check -
tar -xzf runtime.tar.gz -C runtime
server="$(find "$ai_dir/runtime" -type f -name llama-server -print -quit)"
test -n "$server"
"$server" --version
curl --fail --location --retry 2 -o model.gguf \
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
python3 - <<'PY'
from pathlib import Path
with Path("model.gguf").open("rb") as f:
    assert f.read(4) == b"GGUF", "Invalid GGUF header"
print("GGUF header confirmed; publisher model digest NOT independently verified.")
PY
{
  printf '#!/usr/bin/env bash\nset -Eeuo pipefail\n'
  printf 'exec %q -m %q --alias Qwen2.5-1.5B-Instruct-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 2048 -ngl 0\n' \
    "$server" "$ai_dir/model.gguf"
} > "$ai_dir/start-server.sh"
chmod 700 "$ai_dir/start-server.sh"
printf '\nStart manually with: bash %q\n' "$ai_dir/start-server.sh"
printf 'For startup setup: export HIVE_AI_DIR=%q\n' "$ai_dir"
