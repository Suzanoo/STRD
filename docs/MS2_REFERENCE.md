# MS-2 engineering reference and independent evidence

## Source and authority

Accepted source: supplied DPT *คู่มือการออกแบบอาคารเหล็กโครงสร้างรูปพรรณ*, ISBN 978-974-458-597-4. PDF 186 pages, original filename `การออกแบบโครงสร้างเหล็ก2กรมโยธา.pdf`. SHA256 `8e7f8411228698cc3cffdb69ce50e284e4a95f535d48052cb61af0f5c47b95a9`. Printed page p maps to PDF page p+20 in these chapters. The source is not redistributed.

Basis remains this book's ASD/LRFD framework (introduction references ANSI/AISC 360-10), not current regulatory certification. External AISC searches were used for context only; no new standard edition/equation overrides the supplied manual. Relevant images inspected: printed pp.29-30, 52-53, 93-94, 119-120; MS-1 p.91 evidence reused. Extracted text was cross-checked where equation layout, radicals and inequalities matter.

## Verified source inputs

One physical example section, not a catalog. MS-1 geometry/material entries retained unchanged.

| Property | Stored SI value | Source / meaning |
|---|---:|---|
| d, bf, tw, tf | 450, 200, 9, 14 mm | Examples 10.3.1/10.3.2 and 10.4.1 |
| root radius | 18 mm | Clear-web substitution pp.91,119 |
| Zx plastic | 1,621,000 mm^3 | 1621 cm^3 in yielding substitution p.91 |
| Sx elastic | 1,490,000 mm^3 | 1490 x 10^3 mm^3, p.93 |
| ry | 44 mm | Lp substitution p.93; not 44 cm |
| Iy | 18,700,000 mm^4 | 1870 x 10^4 mm^4, p.93 |
| J | 472,000 mm^4 | 47.2 x 10^4 mm^4, p.93 |
| Cw | 890,000,000,000 mm^6 | 0.89 x 10^12 mm^6, p.93 |
| Fy, E | 245, 200000 MPa | pp.74,90,93,119 |
| h0 | 436 mm (derived) | d-tf, p.93 |
| h | 386 mm (derived) | d-2(tf+r), pp.91,119 |
| Aw | 4050 mm^2 (derived) | d*tw, p.119 |

Independent sanity evidence: Zx/Sx=1.087919463 (>1); Cw approximately Iy*h0^2/4 = 888,698,800,000 mm^6, consistent with the stated rounded 0.89e12. This sanity check is not a substitute manufacturer certification. J/Cw/Sx are used as stated book inputs, not reconstructed to force rounded final answers. Legacy CSV Zx=1621.489 is not used. The book table's label Z can denote elastic section modulus; fixture names distinguish Sx elastic and Zx plastic explicitly.

## Provisions and implemented equations

Classification: Table 1(b), rolled flange row 10 / doubly symmetric web row 15. Flange b/tf=bf/(2tf), compact limit .38sqrt(E/Fy), noncompact upper limit sqrt(E/Fy). Web h/tw, compact limit 3.76sqrt(E/Fy), noncompact upper limit 5.70sqrt(E/Fy). Equality at compact limit is compact. Section 5.2 applies only if both components are compact; noncompact/slender branches are rejected, not calculated by 5.2.

Flexure: 5.1 phi_b=.9, Omega_b=1.67, and support twist restraint. Eq.(9) Cb=12.5Mmax/(2.5Mmax+3MA+4MB+3MC), using magnitudes in a segment braced at both ends. The input limit [1,5] is its mathematical envelope when each point lies in [0,Mmax]. No cantilever/free-tip branch is implemented.

Section 5.2: Eq.(10) Mp=Fy*Zx. Define c=1 (17a), h0=d-tf, rts^2=sqrt(Iy*Cw)/Sx (16), a=J/(Sx*h0). Lp=1.76ry*sqrt(E/Fy) (14). Lr=1.95rts*E/(.7Fy)*sqrt(a+sqrt(a^2+6.76(.7Fy/E)^2)) (15).

- Lb<=Lp: Mn=Mp.
- Lp<Lb<=Lr: Mn=min(Mp, Cb[Mp-(Mp-.7Fy*Sx)(Lb-Lp)/(Lr-Lp)]) (11).
- Lb>Lr: Fcr=Cb*pi^2*E/(Lb/rts)^2 * sqrt(1+.078a(Lb/rts)^2); Mn=min(Mp,Fcr*Sx) (12)-(13).

Shear: 6.1 / 6.2.1. Vn=.6Fy*Aw*Cv (94); Aw=d*tw. For rolled h/tw<=2.24sqrt(E/Fy): Cv=1, phi_v=1, Omega_v=1.50 (95). Otherwise phi_v=.9, Omega_v=1.67 and, with unstiffened kv=5 valid only for h/tw<260:

- lambda<=1.10sqrt(kvE/Fy): Cv=1 (96).
- first limit<lambda<=1.37sqrt(kvE/Fy): Cv=1.10sqrt(kvE/Fy)/lambda (97).
- above second limit: Cv=1.51kvE/(lambda^2*Fy) (98).

6.2.2 transverse-stiffener exemption: h/tw<=2.46sqrt(E/Fy), or available strength using kv=5 strictly greater than demand. Equality without the slenderness exemption is reported UNSUPPORTED, not quietly accepted. This is conservatively faithful to the book wording; the verified fixture meets the slenderness exemption. Stiffener design, local concentrated-force checks and tension-field action are excluded.

## Independent numerical evidence

`verification/ms2_reference_calculations.py` is a 50-digit Decimal worksheet with source literals, no production-module imports. It uses weighted endpoints for inelastic interpolation and an algebraically rearranged elastic expression; it also reproduces the book's staged-rounded substitution. Tests compare production values against this worksheet and analytical boundary values, not generated snapshots. Actual worksheet output is included in the delivery evidence.

| Quantity | Independently computed |
|---|---:|
| flange ratio / compact limit | 7.142857143 / 10.857142857 |
| web ratio / compact limit | 42.888888889 / 107.428571429 |
| rts | 52.325666524358 mm |
| Lp | 2212.571428571429 mm |
| Lr | 6594.583800917255 mm |
| Example 10.3.1 Mn | 397.145 kN-m |
| Example 10.3.1 LRFD / ASD | 357.4305 / 237.811377245509 kN-m |
| Example 10.3.2, Lb=3333, printed Cb=1.01: Mn | 364.546373221734 kN-m |
| Example 10.3.2 LRFD / ASD | 328.091735899560 / 218.291241450140 kN-m |
| Example 10.3.2 inner Cb from stated .972,1,.972 | 1.013623094389 |
| Outer Cb from .889,.306,.556,.750 | 1.459386696434 |
| With unrounded inner Cb, Mn | 365.854082052623 kN-m |
| Elastic LTB Lb=10000, Cb=1: Mn | 141.092063531998 kN-m |
| Example 10.4.1 Vn / LRFD | 595.35 kN |
| Example 10.4.1 ASD | 396.9 kN |
| Shear limits (rolled, first, second) | 64; 70.276422149993; 87.526089404992 |
| Synthetic lambda=80 / 100: Cv | .878455276875 / .616326530612 |

Source demands: 10.3.1/10.3.2 ASD 200 and LRFD 310 kN-m; 10.4.1 ASD 350 and LRFD 542.5 kN. All are below their respective supported capacities. Elastic 10m case is an independent equation case, not another printed book example.

## Rounding, ambiguities and boundary resolutions

1. Book p.93 uses rts=52.3, Lp=2213, Lr=6591; full-precision source-input computation gives the values above. The small length differences are traced to intermediate rounding, not treated as bad equations. The p.94 staged substitution gives Mn=364.493035632709 kN-m, displayed as 364.5. Production uses no intermediate rounding and gives 364.546373221734 for the stated Cb=1.01. Both are within the printed one-decimal comparison tolerance 0.05 kN-m. Full-precision Decimal comparison uses relative tolerance 2e-12 / absolute 1e-9 in the quantity's stated units.
2. Cb rounded to 1.01 and the exact factor 1.013623094389 are different inputs. Both are tested and explicitly labeled; the helper does not round Cb to match the book answer. Lb=3333 is the printed example input, not silently replaced with 10000/3.
3. At Lb=Lr the book assigns Eq.(11). For Cb=1 the inelastic value is .7Fy*Sx=255.535 kN-m; the elastic right-hand limit is 255.248579920665 kN-m. The approximately 0.112% downward step is from the rounded published coefficients (1.95,6.76,.078). Keep exact branch ownership and document the step; no unapproved smoothing or equation alteration. Tests use adjacent floating-point numbers around Lp/Lr.
4. At the second shear boundary Eq.(97) gives Cv=1.10/1.37; Eq.(98)'s right-hand limit is 1.51/1.37^2, about 0.199% higher because 1.51 differs from 1.10*1.37=1.507. Preserve the printed formulas and inequalities. The rolled-web threshold also intentionally changes strength factors (1/1.5 to .9/1.67). Tests assert these steps rather than falsely asserting mathematical continuity.
5. Example 10.4.1 says '8.2.1(a)' in its introductory exception reference; Chapter 6 provisions and its following factor calculation identify the applicable rule as **6.2.1(a)**. Record as an editorial cross-reference error; do not use connection Chapter 8 as the shear basis.
6. Book printed Vn=595.4 kN is rounding of 595.35. Production ASD=396.9 is from unrounded Vn, not repeated rounding of 595.4. Test tolerance .05 kN plus 1e-9 floating comparison slack is display-only.

## Verification envelope and limitations

All actual user-facing calculations use the one verified book record. Synthetic geometry/mocked reference faults test formula branches, compactness boundaries, 6.2.2 handling and fail-closed behavior only. These tests do not establish provenance for other H sections or authorize arbitrary catalog ingestion. Other materials, noncompact/slender flexure, stiffened webs, holes/copes, cantilevers and additional section families remain unsupported.

The tests reproduce the legacy short-Lb UnboundLocalError in isolation and prove the verified replacement's short-Lb result. Internal N-mm arithmetic protects against the legacy mixed kN-m/N-mm pathway. Legacy code itself remains unchanged. Accepted MS-1 tests are regression protection, not a repeated request for PO acceptance. The engine does not verify material supply, actual restraint or the analyst's demand model. Book-based verification is not certification for production structural design.
