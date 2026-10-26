# STRD collaboration authority

Read the local contracts in order:
1. [Engineer Contract](ENGINEER_CONTRACT.md)
2. [Engineer Workflow](ENGINEER_WORKFLOW.md)
3. [Coordinator Contract](COORDINATOR_CONTRACT.md)
4. [Git Governance](GIT_GOVERNANCE.md)
5. [Contract alignment provenance and deltas](CONTRACT_ALIGNMENT.md)

These adaptations are authorized by PO's P1 contract-alignment assignment. Governing
intent comes from Progress Studio contracts at pinned revision
9e6c0a7b66ab400fd4bfc51f428042c795d549a5:
[Engineer](https://github.com/Suzanoo/progress-studio/blob/9e6c0a7b66ab400fd4bfc51f428042c795d549a5/docs/ENGINEER_CONTRACT.md),
[Workflow](https://github.com/Suzanoo/progress-studio/blob/9e6c0a7b66ab400fd4bfc51f428042c795d549a5/docs/ENGINEER_WORKFLOW.md),
[Coordinator](https://github.com/Suzanoo/progress-studio/blob/9e6c0a7b66ab400fd4bfc51f428042c795d549a5/docs/COORDINATOR_CONTRACT.md).
Future upstream changes do not automatically override STRD. No unrelated product
contracts are imported. Current PO instructions take precedence over historical status.

PO owns product/platform/scope/acceptance and granular Git authorization. Work owns
engineering implementation and feasible verification; Work performs no Git operations
or GitHub writes and never accesses Legacy Stashes. Read-only GitHub API investigation
is permitted. Coordinator reviews evidence, briefs PO and acts as Git Operator only
under explicit authorization. Acceptance alone does not authorize integration/tagging.

Deliver complete changed files, baseline/manifest, exact commands and actual evidence;
engineering and contract-alignment .txt reports are separate from the implementation ZIP.
Implementation, automated checks, native runtime checks and PO acceptance are distinct.
Stop at the authorized milestone. See P2.md for current scope and remaining gates.
