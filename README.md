# STRD P2 — Safe project workspace

Offline macOS pilot: multiple members, versioned project files, Create/Open/Save/Save As,
recovery and stale-writer protection over the unchanged DPT-based A2 calculations.
P2 is submitted for review; P1 is accepted at `34022de` / `p1-accepted`.

Install the delivered 0.4.0 wheel into `.venv-p2`, then run
`.venv-p2/bin/python -m strd.desktop`. See [setup/use](docs/P2.md),
[verification](docs/TESTING.md), [contracts](docs/COLLABORATION.md).
Python with Tk required. Use local files; no cloud/shared concurrent editing.
Saved drafts are not saved calculation approvals: reopen and recalculate.
No additional engineering scope, reports/release work or P3 is included.
