# STRD — bounded steel strength engine

MS0/MS1/MS2 accepted; A1 package migration submitted for PO review. A2 not authorized.
One verified book fixture only: H450x200x9x14, Fy=245 MPa, E=200000 MPa.
Supports continuous-bracing bending, major-axis bending/LTB, unstiffened web shear,
ASD/LRFD and Cb arithmetic. PASS is conditional on the named check and caller assertions,
not whole-member, bracing-system or production structural-design certification.
No UI, project persistence, analysis, new materials or catalog expansion.

Read [documentation](docs/README.md), [A1](docs/A1.md), [API/envelope](docs/MS2.md),
and [setup/testing](docs/TESTING.md). Python 3.10+ syntax, zero runtime dependencies.
Actual Work runtime: Linux CPython 3.12.14; other runtimes need their own verification.

Dependency-free source test entry:

```sh
python scripts/run_tests.py --source
```

After installing the wheel, from any directory:

```python
from strd import check_bending, check_flexure, check_web_shear, moment_gradient_factor
```

Existing strd_verified imports and the two commands remain compatible after installation:

```sh
python -m strd_verified
python -m strd_verified.ms2_examples
```

The src layout requires installation for normal imports. Typed request/result definitions
are in strd.domain.contracts; runtime validation remains authoritative. Fixed example
records are not a manufacturer catalog. Do not bypass public applicability gates.

Legacy code/catalogs/setup are [archived](archive/legacy/README.md), excluded from the
wheel, not certified by these tests. The existing alignment-chart image is unchanged
and excluded. No source book, public release or new license grant is supplied.
