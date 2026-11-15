#!/usr/bin/env bash
# Sends one local inference request; does not mutate the HIVE database.
set -Eeuo pipefail
: "${HIVE_INSTALL_DIR:?Set HIVE_INSTALL_DIR to the tested HIVE checkout}"
cd "$HIVE_INSTALL_DIR"
test -x .venv/bin/python
printf '\n=== Machine and operating system ===\n'
hostname
cat /etc/os-release
printf '\nBoot ID: '
cat /proc/sys/kernel/random/boot_id
printf '\n=== Service state ===\n'
systemctl --user is-enabled hive-local-ai.service
systemctl --user is-active hive-local-ai.service
systemctl --user show hive-local-ai.service -p MainPID -p ExecMainStartTimestamp
loginctl show-user "$(id -un)" -p Linger
printf '\n=== HIVE and local AI ===\n'
.venv/bin/python -B <<'PY'
import time
from urllib.request import build_opener, ProxyHandler, install_opener
from importlib.metadata import version
from hive.providers.llamacpp import LlamaCppProvider
print("HIVE package:",version("hive-engine"))
opener=build_opener(ProxyHandler({}))
install_opener(opener)
for _ in range(60):
    try:
        with opener.open("http://127.0.0.1:8080/health",timeout=1) as r:
            if r.status == 200:
                break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit("FAIL: Model not ready")
started=time.monotonic()
answer=LlamaCppProvider(
    base_url="http://127.0.0.1:8080/v1",
    model="Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",timeout=90
).chat(messages=[{"role":"user","content":"Reply exactly: HIVE startup verified"}],
       temperature=0,max_tokens=32)
assert answer.strip(), "Empty model response"
print("Response:",answer)
print(f"Elapsed: {time.monotonic()-started:.2f} seconds")
print("PASS: Live local text response received.")
print("Reboot persistence requires evidence from separate boots.")
PY
