#!/usr/bin/env bash
# Newly packaged version; never kills unidentified existing servers.
set -Eeuo pipefail
trap 'printf "\nSTOPPED at line %s; inspect service logs.\n" "$LINENO" >&2' ERR
umask 077
ai_dir="${HIVE_AI_DIR:-$HOME/.local/share/hive-local-ai-b12110}"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
unit="$unit_dir/hive-local-ai.service"
test -f "$ai_dir/model.gguf"
test -f "$ai_dir/start-server.sh"
test ! -e "$unit" || { printf 'STOP: Service exists; nothing overwritten.\n'; exit 1; }
systemctl --user show-environment >/dev/null
python3 - <<'PY'
import socket
with socket.socket() as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1",8080))
    except OSError:
        raise SystemExit("STOP: Port 8080 occupied; stop the identified AI server first.")
PY
case "$ai_dir" in *[!a-zA-Z0-9_./-]*) printf 'STOP: AI path needs a simple absolute path.\n'; exit 1;; esac
case "$ai_dir" in /*) ;; *) printf 'STOP: AI path must be absolute.\n'; exit 1;; esac
sudo loginctl enable-linger "$(id -un)"
mkdir -p "$unit_dir"
cat > "$unit" <<SERVICE
[Unit]
Description=HIVE local Qwen AI server
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=exec
WorkingDirectory=$ai_dir
ExecStart=/bin/bash $ai_dir/start-server.sh
Restart=on-failure
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=default.target
SERVICE
systemctl --user daemon-reload
systemctl --user enable --now hive-local-ai.service
systemctl --user is-enabled hive-local-ai.service
systemctl --user is-active hive-local-ai.service
test "$(loginctl show-user "$(id -un)" -p Linger --value)" = yes
printf '\nEnabled and active; run verify-existing.sh to check model readiness.\n'
printf 'Actual startup after reboot remains UNKNOWN until tested.\n'
printf 'Disable: systemctl --user disable --now hive-local-ai.service\n'
