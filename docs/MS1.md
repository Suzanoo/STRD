# MS-1: reproducible foundation and bounded bending proof

## Current acceptance record

PO accepted MS-1 and reported macOS verification: 21 tests PASS, JSON smoke PASS, merged/pushed to main 4778e38458dac9ea7bf5d94bf2d4b749646350fb, working tree clean. This is accepted PO evidence, not a Work claim of native execution. MS-2 is separately authorized; see [MS-2](MS2.md). The original MS-1 API/envelope below remains unchanged. Historical MS-1 deferrals do not override the later MS-2 authorization.

## Accepted Product Owner decisions

Baseline main 1e1b820f0a30e86fa0fd15ce0f707ac8e2b71468. MS-0 accepted; reuse-first. First target is a rolled doubly symmetric compact H-beam, major-axis bending first and applicable shear subsequently. The supplied DPT manual is the initial ASD/LRFD verification basis. Work is authorized for MS-1 only. UI platform remains undecided. No current-code certification is implied.

## Implemented engineering choice

A standard-library-only source package, strd_verified, implements the continuously braced case in Example 10.3.1. One immutable section/material record is verified for this proof, not a manufacturer catalog. Public API: check_bending(request). A headless example command emits JSON. No install/build system or external runtime dependency is needed for this source-tree proof. Legacy setup.py and every legacy Python/CSV remain unchanged.

Reuse review: applications/flexural.py Yeild.major_axis has useful yielding arithmetic, independently checked in a regression test. Its formula is re-expressed with explicit N-mm units and structured output. Importing the legacy module would also import numpy and carry mixed UI/units conventions. WT logic is reviewed and corrected for this example's clear web H-2(tf+r), rather than reusing the legacy H-2tf blindly. The failing legacy LTB/router and CSV catalog are deliberately not dependencies. This is an extraction of the bounded verified capability, not a competing complete engine.

## Request schema (all fields required; extras rejected)

- basis_id: DPT-STEEL-MANUAL-ISBN9789744585974-EX10.3.1-v1
- section_id: EX10.3.1-H450x200x9x14
- material_id: EX10.3.1-SS400-SM400
- method: exactly ASD or LRFD
- moment_knm: finite nonnegative demand magnitude, already on that method's basis
- continuously_braced: true
- support_twist_restrained: true
- major_axis_only: true

False assumptions are UNSUPPORTED; missing/wrongly typed assumptions are INVALID_INPUT. No defaults silently establish restraint or load suitability. This proof does not infer restraint adequacy from geometry. Unknown section/material/basis/method is UNSUPPORTED; unknown extra actions/properties are rejected rather than ignored. Booleans, numeric strings, NaN/infinity, conversion overflow and negative moments are invalid. Zero demand is valid only with valid positive reference strength.

## Result semantics

PASS/FAIL describes only the supported major-axis bending check. Equality demand=capacity passes, using full precision, not rounded display. INVALID_INPUT and UNSUPPORTED contain no capacity/ratio. not_checked explicitly lists shear, serviceability, connection/local bearing, combined actions/torsion, global stability and bracing adequacy. There is no whole-member or whole-building pass.

Trace includes echoed inputs, basis ID, calculator version, source SHA256, reference values/units, clauses/pages, compactness ratios/limits, nominal/design strengths, demand conversion, utilization, governing state and formulas. Each call returns fresh JSON-compatible data and performs no console/file/network I/O. Reference records are immutable; derived result data does not mutate them.

## Explicitly deferred

Discrete bracing and full LTB equations, other sections/materials, noncompact/slender branches, shear, axial/combined design, connections, analysis, optimization, Save/Open, UI and MS-2+. Existing legacy defects remain unresolved outside this new envelope. Arbitrary Lb/Cb inputs are rejected as unknown fields; no inference of an unbraced proof is allowed.

## Acceptance status

MS-1 accepted as recorded above. Its automated proof does not establish a native Desktop UI or current-code certification. Work performed no Git operations; integration was reported by PO.
