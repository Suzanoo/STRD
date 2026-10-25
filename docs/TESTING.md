# Reproducible A1 verification

Python 3.10+ syntax; actual Work runtime Linux CPython 3.12.14. Use fresh environments.
From repository root, source proof without pip/dependencies:

```sh
python3 -m venv --without-pip .venv-a1-source
.venv-a1-source/bin/python scripts/run_tests.py --source
```

Install delivered wheel (WHEEL_PATH is the extracted handoff wheel location):

```sh
python3 -m venv .venv-a1
.venv-a1/bin/python -m pip install --no-index --no-deps WHEEL_PATH
.venv-a1/bin/python scripts/run_tests.py
.venv-a1/bin/python -m strd_verified
.venv-a1/bin/python -m strd_verified.ms2_examples
.venv-a1/bin/python verification/ms2_reference_calculations.py
```

Windows PowerShell: use py -3 for venv creation and .\.venv-a1\Scripts\python.exe
(or .venv-a1-source) for commands instead of bin/python. Quote paths with spaces.
Native Windows/macOS A1 execution has not been performed by Work.

Full installed-distribution gate (creates/discards a fresh temporary venv itself):

```sh
python scripts/verify_distribution.py WHEEL_PATH
```

Checks exact wheel source contents/metadata, absence of runtime dependencies, offline
installation, isolated Python from outside repo, all tests, optional/legacy dependency
absence and smoke/worksheet output. Default test runner refuses source/editable imports
for installed verification; --source must be explicit. Source-only tests are not enough.

Build in a fresh build venv with pip:

```sh
python -m pip install -r requirements-build.txt
python -m pip wheel --no-deps --no-build-isolation --no-index --wheel-dir dist .
python scripts/verify_distribution.py dist/strd_engine-0.1.0-py3-none-any.whl
python -c "from setuptools.build_meta import build_sdist; build_sdist('dist')"
```

Build setup requires network or trusted wheelhouse. Work used the exact preinstalled
setuptools 84.1.0, wheel 0.48.0, packaging 26.3 and built offline. Runtime needs none.
The sdist includes test/archived evidence; the wheel excludes both.

Verification inventory: 21 MS1 + 25 MS2 accepted methods (only two legacy paths changed),
6 A1 methods covering 527 frozen baseline cases per API, canonical purity/fault rejection,
dependency direction, typed schema and 45 archived file hashes. Frozen responses prove
preservation; unchanged book/Decimal tests independently check numerical correctness.
Private synthetic tests do not authorize more catalog entries.

Original A1 source/installed verification: 52 tests PASS, zero errors/failures/skips.
Both smoke commands: 2 and 7 finite JSON records; worksheet: 23 quantities.
Actual commands/logs and delivery-application evidence are in the handoff ZIP.
Python 3.10 syntax parse is not runtime verification. No static checker, UI/native
acceptance or structural-design certification is claimed. Existing PO acceptance
is not reopened by regression runs. Future engineering scope needs authorization.


## A1 macOS diagnostic portability correction (2026-10-25)

PO Python 3.12.7/macOS source verification found 36 subtest failures in the golden
response method: cases 0370-0378 and 0439-0447, both public APIs. These 18 requests
have Lb near 1e308 mm; float exponentiation raises ERANGE OverflowError before a
capacity exists. The response forwards OS-owned text, which differs between the
observed macOS and Linux runtimes. Status remains INVALID_INPUT.

The test comparator now permits ONLY the two observed complete ERANGE messages for
those exact case IDs. All other dictionary fields and all other cases remain exact;
no tolerance, message stripping, substring matching, fixture regeneration or production
change. Additional tests verify actual native OverflowError/ERANGE, both diagnostic
spellings through both APIs, and rejection of wrong status, capacity, utilization,
exclusions, versions, missing fields, errno, unknown messages and numerical drift.

Corrected suite: 55 methods (original 52 plus 3), all PASS in Work Linux source and
installed-wheel checks. Simulated macOS wording is not native macOS acceptance.
PO repeats the same source command for native confirmation; expected 55 tests PASS.
The original A1 wheel remains valid: runtime/package contents did not change.
Use the existing installed-wheel command; no reinstall/rebuild is required for this
source test/document-only correction. A1 acceptance remains on hold pending PO result.
