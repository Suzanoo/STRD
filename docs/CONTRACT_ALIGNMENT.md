# P1 contract alignment — source, deltas and authority

PO explicitly authorized adoption of applicable Progress Studio contracts into STRD.
Source inspected: Suzanoo/progress-studio main and previously pinned revision both
9e6c0a7b66ab400fd4bfc51f428042c795d549a5. No upstream contract delta was found.
STRD baseline: d232274ff92adcee83cad4256fd55da4bb9a9c8f.

Local adapted contracts now provide one discoverable STRD operating reference:
ENGINEER_CONTRACT.md, ENGINEER_WORKFLOW.md, COORDINATOR_CONTRACT.md, GIT_GOVERNANCE.md.
The upstream source links remain provenance; future upstream changes do not silently
change STRD authority. This delivery is subject to PO acceptance; no Git right is granted.

| Source / section | Treatment in STRD | Reason |
|---|---|---|
| Engineer Contract all role/scope/evidence/acceptance/Git sections | Retained, with source header and desktop wording | Preserve governing intent |
| Engineer Workflow sections 1-11,13-16 | Retained; desktop examples use generic native wording | Same investigation, execution, handoff and stop process |
| Workflow section12 Excel/workbook discipline | Replaced by DPT/source/units/UI freshness and separate verification gates | Excel-specific rules are unrelated to STRD |
| Coordinator Contract roles, briefing, numbered PO questions and granular Git authority | Retained; generic native desktop wording | Coordinator remains reviewer/operator, not PO or engineer architect |
| STRD collaboration pinned links | Replaced by local contract index with exact upstream provenance | Avoid external-only operational dependency and duplicate authority |
| Git governance detail | Explicit branch/baseline/conflict/integration/tag/closure checklist | Clarifies user-requested governance; grants no new operations |
| Work Git boundary | STRD's stricter no-Git-CLI rule retained; read-only API evidence permitted | Upstream allows read-only Git but STRD already forbids Work Git operations |
| A2 submitted/unauthorized P1 status text | Updated current index/instructions; historical evidence retained with status note | Latest PO acceptance/authorization supersedes stale delivery-time status |

No EV, Payment, Excel layout or other Progress Studio product contracts are imported.
No material role or authorization conflict requiring a new PO decision was found.
No requirement is inferred that Work can create branches because implementation is
approved. Coordinator's branch/commit/push/merge/tag permissions remain explicit.

Accepted P1 product decision in this execution: PO selected Desktop on macOS through
the platform question. Work selected Tk/ttk as an implementation decision; framework
choice is not transferred to Coordinator. English pilot labels are an implementation
choice; wider localization/release scope remains D3, not implied by this delivery.

Review gate: Coordinator reviews preserved intent and deltas; PO accepts/revises the
contract-alignment delivery alongside P1. Any material future authority change must be
explicitly proposed and approved, never smuggled into an implementation note.
