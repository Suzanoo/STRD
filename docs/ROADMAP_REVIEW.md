# Roadmap review after A2 — recommendations, not implementation authorization

Accepted history: MS0/MS1/MS2 and A1. A2 is currently submitted for review.
Prior investigation proposed A1 -> A2 -> P1 -> P2 -> P3, then selective extensions.
User authorized review of remaining milestones; none below is authorized to implement.

## Recommendation

Keep the main sequence. A2's supplied sources remove the earlier catalog-access
blocker. No separate broad CSV rewrite or general section-property engine milestone
is necessary before P1: required properties exist for the curated subset. Expand the
catalog through individually verified additions when useful, not blanket legacy import.
Preserve book fixtures independently of manufacturer records permanently.

Clarify P1's handling of multiple cases/segments now that the service supports them:
P1 remains ONE member in memory, with a simple case/segment editor and complete
coverage feedback. It must not flatten the A2 output into a whole-member green PASS.
This is a proposed P1 scope clarification, subject to PO approval; no UI is implemented.

## Main path and gates

| Milestone | Value / scope and deliverables | Dependencies | Verification / acceptance gate | Exclusions / main risks |
|---|---|---|---|---|
| P1 First interactive strength checker | Launchable one-member pilot; selected catalog, case/segment/restraint input, calculate/recalculate, stale-result state, per-check trace and usage guide | A2 acceptance; D2 platform/pilot OS decision | Enter -> calculate -> edit -> stale -> recalculate; incomplete/failed checks distinct; exact engine agreement; real pilot launch and input tests | No durable projects, member collection, solver, optimization or polished exports; risk hiding exclusions and case coverage |
| P2 Safe project workspace | Versioned project files, multiple members, Create/Open/Save/Save As, catalog snapshots, recovery and stale-writer protection; migration policy and sample projects | Accepted P1 | Roundtrip, failed-save, corrupt-file recovery, concurrent-instance rejection, version/catalog drift and native paths/dialogs | No cloud sync/shared concurrent editing; risk data loss and treating old results as current |
| P3 Reports and release readiness | Human-readable reports plus machine-readable assessment export; chosen OS packages, clean install/update policy and documentation | P2; D3 release audience/OS/language/formats; actual data/tooling rights review | Export matches exact snapshot; invalid/stale/incomplete visible; rendered Thai text if selected; offline reopen; update preserves projects; native tests for each claimed OS | No automatic updater, Office report editor, public cloud or certification; rights/rendering/packaging risk |

P1 is still the earliest meaningful working-app test for PO. P3 is the first proposed
complete internal workflow: create/open -> multiple members -> check -> save -> report.
Technical toolkit and serialization choices remain Work's responsibility after PO
chooses user-facing platform/ownership constraints; do not ask PO to prescribe APIs.

## Engineering extensions: choose by need, authorize separately

Each extension delivers source/applicability evidence, independently verified checks,
required bounded data and input/report support. Every gate includes prior regression.

- E1 Additional H checks: choose minor-axis or noncompact flexure etc.; depends on
  A2/P3 and specific basis approval. Gate all applicable limit states for that bounded
  use case. Exclude blanket full-H/bracing/global-stability claims. Risk incomplete scope.
- E2-T Axial tension: gross/net/shear-lag treatment with explicit connection inputs;
  depends on A2/P3 and verified extra inputs. Gate independent rupture/yield/shear-lag
  cases, missing-data rejection. Exclude connection design. Risk invented net area.
- E2-C Axial compression: chosen section and all applicable buckling modes, externally
  justified effective lengths; depends on A2/P3. Gate axis/slenderness/boundary reference
  cases. Exclude frame stability solver/default-K certification. Risk omitted modes.
- E3 Combined actions: same-case signed action tuples and required magnification;
  depends on accepted relevant E1/E2 branches and P3. Gate interactions, limiting cases,
  units and no unrelated-maximum mixing. Exclude unsupported second-order/torsion cases.
- E4 Additional section family: one family/data/basis/task at a time; depends on A2/P3
  and relevant engineering checks. Gate family-specific verification and no H fallback.
  Exclude wholesale CSV import. Risk different thin-wall/fillet/shear-centre assumptions.
- C1 One connection workflow: depends on P3 and selected use case/references; not on
  completing all E milestones. Deliver complete bounded failure-mode coverage. Gate
  independent geometry/spacing/strength cases. Exclude all-connections promise.
- I0 Integration investigation: can move earlier when PO has a concrete force-import
  need; depends on stable action API and selected source workflow. Deliver options,
  source/license/units/axes/case mapping and narrow proof proposal. Gate PO go/no-go.
  Exclude solver/importer implementation. Risk false equivalence of upstream actions.
- I1 Authorized integration proof: only after I0 acceptance and separate authorization.
  Deliver bounded importer OR verified solver adapter, source identity and benchmarks.
  Gate mapping/units/cases; if solver, equilibrium/reaction/deflection independent checks.
  Exclude general building analysis and automatic design-demand certification.

Do not reinstate old bundled MS3-MS6 merely for numbering continuity. They combined
UI/storage/reporting and engineering prerequisites too broadly. Do not interpret this
review as acceptance of every extension or a fixed commitment to all of them.

## PO decisions actually needed

1. Accept/revise A2 subset, evidence and member assessment semantics now.
2. Before P1, D2: desktop vs web and pilot OS. Recommendation remains offline-first
   desktop pilot if local independent use is the priority; web is preferable if browser
   access/central deployment dominates. Deferral does not block A2, but blocks P1 UI.
3. Before P1 authorization, accept/revise one-member multiple-case/segment preview.
4. Before release work, D3: internal pilot vs wider distribution, target OS/language,
   report audience/formats. Defer now; do not promise release rights/OS support prematurely.
5. Later, prioritize an actual engineering limitation/integration use case before
   authorizing any E/C/I scope. No choice is required to complete A2.
