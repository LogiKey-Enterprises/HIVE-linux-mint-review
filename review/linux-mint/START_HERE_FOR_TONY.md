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
| Actual reboot persistence | One operator-reported reboot checked; enabled/active service and live response |
| Recurring monitoring | Installed, timer active; first availability + instruction sample passed in 1.117 s |
| Sustained reliability / actual recovery | UNKNOWN |

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

Acceptance remains bounded: one post-reboot check passed. Observe later scheduled samples and test monitoring persistence before any sustained-reliability claim; actual crash recovery remains UNKNOWN.

## November 15 update — reboot verified; monitoring started

Machine: broxson-mobile, documented Linux Mint 22.3 Xfce. Evidence: operator-pasted terminal output.

- Reported reboot: 2026-11-15 14:05:10 CST. AI service started at 14:05:17 CST (7 seconds later), PID 1200; enabled, active, Linger=yes.
- The check did not start the server manually. HIVE received a live response after reboot: one reboot persistence check PASSED.
- Instruction-following FAILED that reboot prompt: the model described unrelated Apache Hive rather than returning the requested phrase. Availability success must not be reported as instruction-following success.
- Reliability timer installation then completed. Timer hive-reliability.timer was active, next check about five minutes later.
- First observation: 2026-11-15T20:20:59.307768+00:00 (14:20:59 CST), boot ID 46c57fc0-a187-4cd0-8d03-fc773016ea8e.
- Sample 1: availability=true; exact instruction=true; response HIVE_OK; 1.117 seconds; failure_streak=0; recovery=none.

### Implemented monitor policy

Every five minutes while awake: check service state, HTTP /health and one short HIVE provider inference request. Record availability and exact instruction-following separately, with response time and boot ID. Rotating JSONL history (2 MB per file, three backups), latest JSON and cumulative state are local only.

Two consecutive availability failures permit a restart only if the AI service is enabled, the 30-minute recovery cooldown has elapsed and fewer than three attempts have occurred that UTC day. An incorrect nonempty response does not trigger restart. A successful restart command is only a recovery request; the next sample must verify availability. A failed availability request's instruction result is unknown, not an instruction pass.

Paths on operator machine: ~/.local/share/hive-reliability/{check.py,checks.jsonl,latest.json,state.json}; user units hive-reliability.service and hive-reliability.timer.
Pause monitoring: systemctl --user disable --now hive-reliability.timer, then systemctl --user stop hive-reliability.service.

### Evidence limits and next acceptance

One reboot is verified; only ONE monitor sample is available in this conversation. Later scheduled firings, monitoring persistence across another reboot, sustained reliability and actual recovery after failure remain UNKNOWN. The first monitor run was explicitly triggered by its installer; an active timer does not prove later firings. No failure was induced and no recovery occurred. No 24-hour success claim or notification delivery is implied.

Next: review the existing local history after an observation window, assess availability and instruction-following separately, and inspect gaps/suspend periods. Confirm monitoring's own persistence at the next normal reboot. The HIVE Mint Desktop and applications-menu launcher files were created successfully, based on operator-pasted output: Created HIVE Mint in your applications menu and on your Desktop. Launcher activation and opening the icon after reboot remain UNKNOWN. The launcher opens an interactive terminal using the existing HIVE virtual environment and local-state database; it does not start another AI server.


Launcher files on Mint: ~/.local/share/hive-launcher/terminal.rc, ~/.local/share/applications/HIVE-Mint.desktop and HIVE-Mint.desktop in the configured Desktop directory. If the desktop requires trust confirmation, allow launching; the actual GUI interaction is not yet evidenced.
