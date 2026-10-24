# MS-2: verified bounded H-beam bending and shear

## Authority and status

PO accepted MS-1, including 21 automated tests and JSON smoke on macOS, and authorized MS-2 only on 2026-10-24. Accepted and remotely verified baseline: `main @ 4778e38458dac9ea7bf5d94bf2d4b749646350fb`. The working tree was clean at PO acceptance (PO evidence). Work uses a source snapshot, performs no Git operations and never accesses Legacy Stashes. MS-2 implementation is submitted for Coordinator review and PO acceptance; it is not yet accepted. MS-3 is not authorized. Desktop/Web remains undecided.

## Engineering choice and supported envelope

Extend `strd_verified` with two pure, independent strength checks and a moment-gradient helper. Preserve `check_bending`, its data, its smoke command and all 21 original tests. Standard library only, source-tree execution; no framework, UI or installation redesign.

The public MS-2 APIs accept **one verified section/material fixture**: rolled, doubly symmetric H450x200x9x14, with the supplied book's Fy=245 MPa and E=200000 MPa. This is the same section in Examples 10.3.1, 10.3.2 and 10.4.1. Lb, Cb and demand are variable; capacities are not hard-coded example answers. No other section or material IDs, property overrides, legacy CSV data or arbitrary catalogs are accepted. [Reference evidence](MS2_REFERENCE.md) records every property and its precision.

- Flexure: major axis, compact flange AND compact web, prismatic undamaged section without holes/copes, both ends of the evaluated unbraced segment braced, and beam supports restrained against longitudinal twist. Evaluate each segment separately using its maximum absolute moment. All three LTB length regions and the plastic-strength cap are implemented. No cantilevers or unbraced free ends are supported. Cb=1 is a conservative input; higher Cb requires caller-verified moment-diagram provenance.
- Shear: web-plane shear in an unstiffened rolled H; no tension-field action or stiffener strength credit. The implemented equation kernel covers the rolled-web exception, other yielding, inelastic buckling and elastic buckling for h/tw<260. **The sole public fixture falls in the rolled-web exception.** Other shear regions are independently tested using synthetic internal geometry, not promoted into a verified commercial catalog.
- Noncompact/slender flexural sections are classified and rejected; Chapters 5.3-5.5 are not silently extrapolated. Supporting these sections would need verified data and additional authorized checks.

This bounded data decision avoids enlarging the catalog without evidence. It is an engineering implementation choice for MS-2 review, not a claim that all rolled H sections are supported.

## Public API

Import `check_flexure`, `check_web_shear`, `moment_gradient_factor` from `strd_verified`. Each accepts one plain dictionary and returns a fresh JSON-compatible dictionary. There is no console/file/network I/O. Complete runnable examples: `strd_verified/ms2_examples.py` and `python -m strd_verified.ms2_examples`.

All fields below are required; unknown extra fields are rejected. No implicit load combinations, unit guesses, type coercion or engineering defaults.

| Common field | Required value/meaning |
|---|---|
| basis_id | `DPT-STEEL-MANUAL-ISBN9789744585974-H-BENDING-SHEAR-v1` |
| section_id | `EX10.3.1-H450x200x9x14` |
| material_id | `EX10.3.1-SS400-SM400` (book fixture, not material selection) |
| method | Exactly `ASD` or `LRFD`; demand already belongs to that basis |
| prismatic_undamaged | Boolean true; includes no holes, copes, taper, damage or section modification |

Additional `check_flexure` fields:

| Field | Meaning |
|---|---|
| moment_knm | Finite nonnegative maximum absolute segment moment, kN-m |
| unbraced_length_mm | Finite nonnegative Lb, mm; zero explicitly means continuous restraint |
| cb | Finite numeric value in [1,5]; this bound follows nonnegative magnitudes in Eq.(9), not an arbitrary code cap |
| cb_source | `CONSERVATIVE` (requires cb=1), or `VERIFIED_MOMENT_DIAGRAM` |
| cb_reference | Nonblank source/assessment description, retained verbatim for traceability |
| support_twist_restrained | Boolean true, book 5.1 support assumption |
| segment_ends_braced | Boolean true, required lateral/torsional restraint at both segment ends |
| major_axis_only | Boolean true, applicable bending orientation; does not certify absence/adequacy of other actions |

Additional `check_web_shear` fields:

| Field | Meaning |
|---|---|
| shear_kn | Finite nonnegative web shear magnitude, kN |
| web_plane_only | Boolean true |
| unstiffened_web | Boolean true; stiffener-dependent cases rejected |

`moment_gradient_factor` takes exactly `maximum_knm`, `quarter_knm`, `midpoint_knm`, `three_quarter_knm`: absolute finite nonnegative values from the same segment and demand basis. Quarter-point values cannot exceed the asserted true maximum. It calculates Eq.(9), without generating forces. A zero diagram returns conservative Cb=1. Values are normalized before summation to avoid overflow. Result `CALCULATED` only establishes arithmetic, not a strength PASS or validation of the actual diagram/restraints. Its unrounded `cb` may be passed to flexure with `VERIFIED_MOMENT_DIAGRAM` and a trace reference. Direct Cb input permits the book's rounded 1.01 comparison. Caller assertions and strings do not prove bracing adequacy or correctness of the analysis.

## Units and numerical policy

Internal N, mm, MPa=N/mm^2. Output capacities kN-m or kN. 1 kN-m=1e6 N-mm; 1 kN=1000 N. Section plastic Zx and elastic Sx are distinct. Aw=d*tw uses overall depth; web slenderness uses clear h=d-2(tf+r).

No intermediate/display rounding in calculations. Full-precision capacity in the public unit is used for comparison so passing the reported capacity back as demand is equality; the next representable higher demand fails. Display comparison tolerances are never design acceptance tolerances. NaN, infinity, numeric strings, booleans-as-numbers, negative magnitudes, conversion overflow and unusable numerical ranges are rejected. No zero/invalid capacity is replaced with 1. Extremely long lengths that overflow/underflow arithmetic are rejected, not clamped.

Book branch ownership is retained: Lb<=Lp yielding; Lp<Lb<=Lr inelastic; Lb>Lr elastic. The authorization's Lb>=Lr region is tested at equality and both sides; equality uses the accepted book's Eq.(11). Rounded equation coefficients cause small specified boundary steps, documented in [reference evidence](MS2_REFERENCE.md); there is no undocumented smoothing.

## Result interpretation

- `INVALID_INPUT`: malformed/missing/extra data or numerical/reference integrity failure. No capacity/utilization.
- `UNSUPPORTED`: unrecognized basis/section/material/method, unmet assumptions, unsupported classification or engineering condition. No capacity/utilization.
- `FAIL`: applicable valid calculation, demand exceeds capacity. Detailed engineering trace retained.
- `PASS`: applicable valid **individual** strength comparison only. Does not certify a complete member.

Results include echoed inputs, source SHA256, property units in names, equation/page references, assumptions, intermediate values, selected ASD/LRFD capacity, utilization and governing state. Flexure reports yielding versus inelastic/elastic LTB and candidate/capped strengths. Shear reports Cv/kv, slenderness boundaries, factors, area, strength, and 6.2.2 stiffener exemption. If a hypothetical thin web reaches capacity equality but does not satisfy the slenderness exemption, the strict 'capacity greater than demand' alternative is not established; return UNSUPPORTED rather than PASS. This does not affect the verified section.

`not_checked` always lists unperformed checks. Flexure does not certify shear; shear does not certify bending. Neither verifies combined action, axial/minor-axis/torsion, global stability, brace design, deflection, connections, net-section rupture, concentrated-force bearing/crippling, fatigue, seismic or fire. Separate checks are not a whole-member interaction or structural analysis. Strength failures do not trigger section optimization.

## Reuse and compatibility

Reuse the MS-1 immutable geometry/material record and strict scalar validator; extend the section record with five book-verified LTB properties. No accepted MS-1 calculation code or tests were rewritten. Exporting additional functions has no I/O side effects. MS-1 results retain their original basis/version and shear exclusion.

Legacy `LTB.hc_major` equations were inspected. Its below-Lp uninitialized Mn failure is reproduced by isolated AST test, then the new independent path is checked. Its mixed nominal-moment units and boundary routing are not imported. The new kernel uses N-mm consistently and covers exact boundaries. Legacy Cb arithmetic is the Eq.(9) candidate, re-expressed with validation/overflow protection. Legacy files themselves are unchanged; their defects and behavior are not declared repaired or certified. No dependency on numpy/pandas/setup.py is introduced.

## Remaining gates

Coordinator reviews evidence and bounded applicability; PO accepts/revises MS-2. PO controls application of the files and Git integration. No additional product/design-basis decision blocks this delivery. Expanding the section catalog, platform selection, production-code certification and MS-3 remain outside this authorization. Automated evidence is not native Desktop acceptance.
