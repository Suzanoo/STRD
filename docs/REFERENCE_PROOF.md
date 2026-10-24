# Engineering evidence: Example 10.3.1

## Source identity

Supplied file: การออกแบบโครงสร้างเหล็ก2กรมโยธา.pdf
Title: คู่มือการออกแบบอาคารเหล็กโครงสร้างรูปพรรณ, Department of Public Works and Town & Country Planning.
ISBN 978-974-458-597-4; PDF 186 pages.
SHA256: 8e7f8411228698cc3cffdb69ce50e284e4a95f535d48052cb61af0f5c47b95a9.
Book introduction references ANSI/AISC 360-10. This is the supplied book's basis, not a claim of current regulatory compliance. Book not redistributed in this payload.

References: printed p.74 general example material assumptions; pp.90-91 Example 10.3.1 (PDF 110-111); p.28 sections 5.1/5.2; p.29 section 5.2.1 Eq.(10); Table 1(b) / 2.4 for classification. Printed p.91 visually inspected against extracted text.

## Minimal verified data

| Property | Value | Unit | Provenance/meaning |
|---|---:|---|---|
| H | 450 | mm | Example 10.3.1 geometry, p.90 |
| B | 200 | mm | Same |
| tw | 9 | mm | Same |
| tf | 14 | mm | Same |
| root radius r | 18 | mm | Clear-web expression, p.91 |
| Zx plastic | 1621 | cm^3 | Fy*Zx substitution, p.91; stored as 1621000 mm^3 |
| Fy | 245 | MPa | Example substitution p.91 / default p.74 |
| E | 200000 | MPa | Classification substitution p.90 / p.74 |
| phi_b | 0.90 | dimensionless | 5.1 and example |
| Omega_b | 1.67 | dimensionless | 5.1 and example |
| ASD demand | 200 | kN-m | Example p.90 service moment |
| LRFD demand | 310 | kN-m | Example p.90 factored moment |

The 10 m span describes the source example but is not used by the pure continuously braced strength equation; no load solver or deflection is inferred. No Ag, rx, Iy, J, Cw, Sx or Fu is needed for this bounded proof. These are intentionally absent.

The example's 1621 cm^3 is a rounded source value. We verify results from that stated value; we do not claim manufacturer precision. Legacy CSV Zx=1621.489 is NOT used. Table columns named Z may represent elastic S elsewhere in this book; this fixture is explicitly the plastic modulus from the example's yielding equation, not a name-based conversion of a legacy column.

## Independent arithmetic (reference literals, not production constants)

b/tf = (200/2)/14 = 7.142857142857143.
Clear web h = 450 - 2(14+18) = 386 mm.
h/tw = 386/9 = 42.888888888888886.
sqrt(E/Fy) = sqrt(200000/245) = 28.571428571428573.
Flange compact limit = 0.38*sqrt(E/Fy) = 10.857142857142858.
Web compact limit = 3.76*sqrt(E/Fy) = 107.42857142857143.
Both ratios are below compact limits.

Mn = 245 N/mm^2 * 1621000 mm^3 = 397145000 N-mm = 397.145 kN-m.
LRFD = 0.90*Mn = 357430500 N-mm = 357.4305 kN-m.
ASD = Mn/1.67 = 237811377.245508982... N-mm = 237.811377245508982... kN-m.
Use independent Decimal arithmetic in tests. Nominal and LRFD intermediate values are checked exactly; ASD float differs from Decimal by at most floating-point precision (asserted to 6 decimal places in N-mm).
Book prints 397.1, 357.4, 237.8 kN-m. Display-reference tolerance is 0.05 kN-m, reflecting one-decimal rounding; this tolerance is NOT used for pass/fail decisions.

The book explicitly omits LTB for this continuously braced example. We require that assumption and support twist restraint explicitly; no Lp/Lr/continuous-brace design is computed. Noncontinuous bracing is unsupported, not a fallback yielding calculation.

## Validation/proof boundaries

Scalar integrity and positive geometry/capacity are validated; classification is calculated. Fixed fixture identity prevents unreviewed catalog selection. Checks do not establish steel supplied on site, actual bracing, full cross-section survey or compliance of another standard edition. New records or scope require separate verification and authorization.

## Regression interpretation

The legacy yielding arithmetic is verified in isolation using AST extraction of the original class with its source inputs; this is reuse evidence only. Legacy LTB's short-Lb error is not patched: the new continuous-brace branch is exercised by the reference tests, and every unsupported restraint is rejected. Zero capacity cannot be replaced with 1 in the new engine. Tests cover full-precision unit conversion, omitted/extra fields, zero/nonfinite inputs, limits, unsupported cases, deterministic output and mutation isolation. No general legacy regression pass is claimed.
