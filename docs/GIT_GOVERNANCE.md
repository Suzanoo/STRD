# STRD Git governance, integration and milestone closure

Authority: PO P1 contract-alignment authorization; applies with ENGINEER_CONTRACT,
ENGINEER_WORKFLOW and COORDINATOR_CONTRACT. This documents their intent for STRD;
it does not grant any Git operation. No change to role ownership is implied.

## Roles and approval scopes

- PO chooses product/platform/scope, accepts milestones, authorizes specific Git actions.
- Work Engineer investigates, designs, implements, tests and delivers complete files
  and separate reports. Work performs no Git CLI operations or GitHub writes, including
  branch creation/switching, commits, stashes, reset/clean, merges, pushes or tags.
  Read-only GitHub API inspection of repository/commit/tag evidence remains permitted.
- Coordinator is Git Operator only within explicit PO authorization. Acceptance of code
  is not Git authorization. Git authorization does not authorize the next milestone.

Existing legacy stashes must not be inspected, applied, dropped, modified or migrated
by Work. Coordinator must also preserve them unless PO separately authorizes an exact
stash operation. A dirty tree is not permission to stash or discard user work.

## Baseline and branch management

Work records repository, accepted base SHA, observed remote branch/tag evidence and
any inability to inspect the user's local tree. Never claim a remote read establishes
local cleanliness. Coordinator checks local branch, upstream and worktree before applying.

Coordinator may create a milestone branch from the verified accepted base only when
PO's Git scope permits branch creation. A descriptive name such as p1-desktop is a
recommendation, not an existing branch or an instruction to Work. Do not assume direct
main work or force-push permission. Branch deletion requires authorization too.

If HEAD differs, compare the relevant delta and stop conflicting application. Preserve
unrelated edits. Do not reset, clean, rebase, stash or cherry-pick as an implicit repair.
No branching model is allowed to bypass milestone review or existing repository rules.

## Integration sequence

1. Work delivers complete changed files, before/after manifest, exact base, test logs,
   limitations, acceptance instructions and standalone engineering/contract reports.
2. Coordinator reviews scope/contract compliance and briefs PO with numbered acceptance
   questions. Reviews and disposable application tests do not authorize commits.
3. PO accepts/revises the milestone and explicitly states the Git actions authorized.
4. Coordinator re-verifies baseline/local changes; applies reviewed payload; runs required
   integration checks. Material changes after acceptance go back for review.
5. Coordinator performs only authorized branch/commit/merge/push actions and verifies
   resulting commit, target branch, upstream state and exact scope. No force push by default.
6. Coordinator reports actual evidence. A local commit is not proof of a push; a push is
   not proof of merge; a tag name is not proof it points to the accepted commit.

Commit messages identify the milestone and resulting behavior. Work may propose a
message but does not execute it. Do not commit environment folders, delivery archives,
full source PDFs or screenshots into production merely because they exist in a handoff.

## Tags, release and closure

An acceptance tag is optional unless PO requests it. Tag creation, moving/deleting a
tag, pushing tags, publishing a release and deployment each require matching authority.
Use a milestone-specific tag only after PO acceptance and verification of its target
commit. Record annotated/lightweight type and signing status accurately; never infer
signature verification from the tag name. Never move an accepted tag silently.

Coordinator closes a milestone by recording:
- PO acceptance reference and date;
- completed and deferred gates, including native-runtime evidence;
- final commit and branch; push/merge evidence when authorized/performed;
- optional authorized tag and resolved commit; release state if applicable;
- remaining limitations and next decision, with no automatic next-milestone permission.

Useful states: AUTHORIZED -> IMPLEMENTED -> WORK VERIFIED -> PO ACCEPTED ->
INTEGRATED -> CLOSED. Tag/release are separately recorded actions, not synonyms for
acceptance. A milestone with an expressly deferred gate must say so; an unexecuted
native gate cannot be reported PASS. Corrections reopen the relevant review/gates.

## Current recorded baseline

PO accepts A2 at d232274ff92adcee83cad4256fd55da4bb9a9c8f. Read-only remote evidence
on 2026-10-25: main points there; annotated a2-accepted tag object
 dd40fa11106eedb732ab16c50caf8c9241c3b547 resolves to that commit. GitHub reported it
unsigned, not a verified signature. Work did not create or modify the tag or inspect
local stashes/worktree. P1 implementation and contract alignment are authorized;
P1 acceptance, Git integration, P2 and releases are not authorized by this document.
