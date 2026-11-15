# HIVE on Linux Mint 22.3 Xfce — review for Tony

November 15, 2026. Operator: Chancellor Chambers. Machine: broxson-mobile.
This is the Mint machine, not the separate Ubuntu MacBookPro14,3.

## Evidence and scope

Evidence comes from operator-pasted terminal output, not direct remote inspection or CI.

| Check | Observed result |
| --- | --- |
| Python | 3.12.3; venv, ensurepip, sqlite3, ssl available |
| Tested HIVE revision | 4d00a485120607f70b078301dfb8f008ad14ba53 |
| Editable installation / pip check | Successful; no broken requirements |
| Automated tests | 41 passed in 7.44 seconds |
| Inspection | 20 Python files, 0 skipped, 185 symbols |
| Import graph | 20 files considered, 70 relationships |
| Dependency query | hive/cli.py imports retrieved |
| Registry | 1 repository (HIVE itself), 0 capabilities |
| AI runtime | llama.cpp b12110 / cd959bae9; CPU only |
| Model | Qwen2.5-1.5B-Instruct Q4_K_M GGUF |
| Live HIVE provider request | "HIVE local AI connected"; 1.25 seconds |
| systemd handover | Enabled, active, response "HIVE startup verified" |
| Before-login startup configuration | Linger=yes asserted by successful setup script |
| Actual reboot persistence | UNKNOWN |
| Repeated reliability / crash recovery | UNKNOWN |

Mint 22.3 Xfce is supported by the existing broxson-mobile continuity record; /etc/os-release was not freshly captured in this session. The runtime archive digest matched the GitHub release asset. The model GGUF header was checked, but its publisher digest was not independently verified.

The fork includes upstream changes newer than the tested pin. The 41-test result must not be attributed to the current fork head or to unexecuted review scripts.

## Review files

- [evidence.json](evidence.json): structured observation receipt.
- [install-core.sh](scripts/install-core.sh): isolated, pinned reproduction with tests and self-inspection.
- [install-local-ai.sh](scripts/install-local-ai.sh): official CPU runtime and model; generates a launcher.
- [enable-autostart.sh](scripts/enable-autostart.sh): loopback-only user service with lingering.
- [verify-existing.sh](scripts/verify-existing.sh): service state, boot ID, health, live HIVE response.

These scripts are NEW reusable packaging of the successful commands. Their shell syntax and embedded Python syntax were checked during preparation; their exact packaged form has NOT been run end-to-end on a fresh laptop. No HIVE application code was changed. Installers write files and download software/model weights; startup setup requires sudo for lingering.

## Suggested reproduction

1. Review this note, evidence.json and the scripts.
2. On a separate Mint test account/machine run bash review/linux-mint/scripts/install-core.sh. Set HIVE_INSTALL_DIR to the exact installation directory it prints.
3. Run bash review/linux-mint/scripts/install-local-ai.sh. Default AI files: ~/.local/share/hive-local-ai-b12110.
4. Run bash review/linux-mint/scripts/enable-autostart.sh.
5. Run bash review/linux-mint/scripts/verify-existing.sh.
6. Reboot normally and rerun verification; record boot ID, service PID and live response before claiming reboot persistence.

This review package does not merge the financial fork, install a hosted API, grant model autonomy, or establish reasoning quality/governance compliance.

## File comparisons and troubleshooting history

Three older copies (Desktop project folder, loose Desktop project files and USB project folder) had the checked core files matching the tested installation, but lacked five AI additions. The financial-review fork lacked graph-related baseline files and differed in five checked files. This indicates another version/fork, not proof the financial work is defective. All checked Python files had zero syntax/read errors.

The first source search missed Desktop projects; "not found" was scoped to that search. Dragging Python source files into Terminal attempted to execute the first path, producing Permission denied; chmod was unnecessary.

The first live AI request failed with connection refused on 127.0.0.1:8080. A follow-up check found no server/model in the searched locations. Downloading the CPU runtime and model, then starting the server, resolved it.

## Documentation finding

The README at the tested revision says HIVE has no source analyzer and describes networking only for discover. Actual inspect/graph behavior and the optional HTTP AI provider supersede those statements. A focused README/install-guide correction is worth review.

## Operation and limits

Service: hive-local-ai.service. Endpoint: http://127.0.0.1:8080/v1.
Status: systemctl --user status hive-local-ai.service --no-pager.
Logs: journalctl --user -u hive-local-ai.service -n 50 --no-pager.
Disable: systemctl --user disable --now hive-local-ai.service.
Do not disable lingering globally without checking other user services.
The installers do not migrate ~/.hive/hive.db.
Suspend pauses inference; login-encrypted home directories may prevent before-login loading.
Zero capability records is expected: inspection does not promote capability claims.

Acceptance remains bounded: complete one post-reboot verification, then decide whether to adopt the small documentation/startup additions upstream. Reboot and crash tests remain UNKNOWN.
