# A2 section and material evidence

## Source manifest and selection

User supplied both original PDFs on 2026-10-25. Rendered table headers/units,
selected rows, diagrams and formulas were inspected. Full PDFs are not redistributed.
The runtime JSON includes source identities and immutable content checksum, not images.
This is a bounded factual subset for the authorized handoff, not a license grant to
republish SYS catalogs or an assertion that commercial distribution rights were audited.
P3 public distribution must review rights for its actual scope.

| Source | SHA256 | Printed / PDF pages used |
|---|---|---|
| SYS-Catalog-Engineer-Edit6.pdf | b60c8c729cefa31075cfd9836af77dc1f644ddd89bd853b8dd09419b984a0458 | 6/8 material; 8/10 definitions; 15/17 dimensions; 16/18 properties; 17/19 audit formulas |
| SYS-Catalog-Thai-Effective-August2026.pdf | 8d55c8575a1c744e919e6e7affef934f9afb5b347331d4724db6fba238a7c59a | 2/4 material; 5/7 H dimensions/elastic properties |
| Accepted DPT book ISBN9789744585974 | 8e7f8411228698cc3cffdb69ce50e284e4a95f535d48052cb61af0f5c47b95a9 | Existing MS2_REFERENCE.md, unchanged basis/proof |

Two ordinary unstarred rows selected: H450x200x9x14 and H500x200x10x16. They have
complete required properties, compatible SS400 thickness, and matching dimensions,
Sx/Iy/ry in both supplied SYS sources. Restricting to two is a deliberate verified
initial subset, not an import failure or a claim that other H sections are unsuitable.
No catalog is inferred from the unverified legacy CSVs. No manufacturer availability,
actual dimensions/tolerances or material certificate is guaranteed by nominal tables.

## Exact source mapping

SYS Engineer uses X-X as major axis, Y-Y minor. Dimensions and fillet radius are mm.
Thai product table's Zx is ELASTIC section modulus (consistent with 2Ix/H); Engineer
uses Sx elastic and Zx plastic. Identical column spelling across documents does not
establish identical meaning. Runtime retains the established unambiguous property names.
`elastic_modulus_x_mm3` means elastic SECTION modulus, not Young's modulus E in MPa.

| Quantity | Source unit | H450 row | H500 row | Runtime field / conversion |
|---|---|---:|---:|---|
| d | mm | 450 | 500 | depth_mm |
| bf | mm | 200 | 200 | width_mm |
| tw | mm | 9 | 10 | web_mm |
| tf | mm | 14 | 16 | flange_mm |
| r (fillet) | mm | 18 | 20 | root_radius_mm |
| Sx elastic | cm^3 | 1490 | 1910 | elastic_modulus_x_mm3, x1000 |
| Zx plastic | cm^3 | 1680 | 2180 | plastic_modulus_x_mm3, x1000 |
| ry | cm | 4.40 | 4.33 | radius_y_mm, x10 |
| Iy | cm^4 | 1870 | 2140 | inertia_y_mm4, x10000 |
| J | cm^4 | 56.9 | 85.9 | torsion_j_mm4, x10000 |
| Cw | cm^6 | 889000 | 1250000 | warping_cw_mm6, x1000000 |

All dimensions from Engineer p15, other properties p16. Material Fy=245 MPa for
SS400 t<=16 mm from Engineer p6, cross-checked Thai p2; both web/flange tested against
that bound. E=200000 MPa comes from the accepted DPT basis, not from a foreign code.
No substitution of a thicker material's lower Fy or a different grade is implemented.

JSON rather than CSV holds the bounded source manifest/material/records together.
Its shape is internal and versioned. A content checksum rejects unreviewed edits;
changing the data requires source review, updated revision/checksum and verification.
No need to modify every legacy consumer because none reads this new data. Archive
files remain historical evidence; only the supported new API exposes this subset.

## Independent checks and discrepancy resolution

`verification/a2_reference_calculations.py` uses independent source literals and
50-digit Decimal arithmetic without production imports. It derives root-fillet
area/first moment, plastic modulus, SYS p17 J and Cw, and checks DPT strength equations.
Production uses the published table values, not reconstructed numbers fitted to tests.

| Audit quantity | H450 | H500 |
|---|---:|---:|
| Area including fillets, mm^2 | 9676.123980 | 11423.362939 |
| Zx without fillets, mm^3 | 1621489 | 2096360 |
| Zx with fillets, mm^3 | 1679054.928186 | 2175173.002186 |
| J from SYS formula, mm^4 | 569105.633701 | 858797.037981 |
| Cw = Iy*(d-tf)^2/4, mm^6 | 888698800000 | 1253269600000 |

These reproduce the displayed manufacturer values within their rounding resolution.
Zx half-step is 5000 mm^3, J half-step 500 mm^4. Cw half-step is 5e8 mm^6 for
889000 cm^6 and 5e9 mm^6 for 1250000 cm^6. These data transcription/display tolerances
are NOT used to make strength utilization pass. Published ry and Sx are retained at
the source precision; no attempt to create extra precision from rounded area/inertia.

The accepted book fixture H450 uses Zx=1621000 and J=472000 mm^4; SYS uses 1680000
and 569000. The no-fillet geometric Zx=1621489 closely explains the book/legacy Zx,
while fillet-inclusive Zx agrees with SYS. The SYS J formula explicitly includes
additional geometry terms and reproduces SYS J. This supports the source distinction;
it does not prove the exact historical derivation of the book's rounded J, and no
claim is made that the book is erroneous. Book Cw=890000000000 is also retained.
The two source records must never be merged just because dimensions match.

Engineering policy: book-example regression tests keep their literal inputs and
expected answers. Manufacturer assessments use their own source-ID/revision/snapshot
and the SAME accepted DPT equations, factors, applicability and numerical policies.
No silent switch to SYS capacity tables, newer AISC equations or SYS's generic Cv=1
statement. The DPT shear calculation still evaluates its actual applicable branch.

## Independently established strength values

Fy=245 MPa, E=200000 MPa, Cb=1, published SYS properties, no intermediate rounding:

| Quantity | H450 | H500 |
|---|---:|---:|
| Lp mm | 2212.571428571 | 2177.371428571 |
| Lr mm | 6803.770568058 | 6843.635128538 |
| rts mm | 52.310962106 | 52.037241076 |
| Mn Lb=1000 mm, kN-m | 411.6 | 534.1 |
| Mn Lb=4000 mm, kN-m | 350.841354704 | 453.428049977 |
| Mn Lb=10000 mm, kN-m | 150.495774037 | 195.755398380 |
| Vn = LRFD shear capacity, kN | 595.35 | 735 |
| ASD shear capacity, kN | 396.9 | 490 |

Flexure LRFD=.9Mn, ASD=Mn/1.67. For these rolled webs shear phi=1, omega=1.5.
Both sections' three Lb regions and both methods are checked against the independent
worksheet (relative 2e-12, absolute 1e-9 in each quantity's units). Boundary ownership,
Cb plastic cap, continuous restraint and exact demand/capacity comparison are tested.
Inherited published-coefficient Lr/Cv steps remain unchanged; see MS2_REFERENCE.md.
All material, source, nominal-geometry and unperformed-check limitations still apply.
