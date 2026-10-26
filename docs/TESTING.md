# Current P2 verification

P1 and contracts accepted at 34022de; native P1 acceptance is not reopened.
P2 regression runs preserve accepted behavior and add project safety evidence.

```sh
python3 scripts/run_tests.py --source
python3 scripts/run_gui_tests.py --source
python3 scripts/verify_distribution.py /PATH/strd_engine-0.4.0-py3-none-any.whl --gui
```

P2 totals after macOS portability correction: 115 headless methods (87 accepted +28 project), 25 real Tk methods
(12 accepted +13 project). Final actual totals are in the separate handoff and logs.
Installed verification uses a clean offline venv outside source and runs the same suites.
Without --gui, distribution checks remain headless. No display/Tk returns NOT EXECUTED
and nonzero, not a passing skip. macOS is the pilot; POSIX locking is required for saves.

Tests include exact draft roundtrip, no persisted results, catalog/version rejection,
corrupt/malformed input, real two-process saves and abrupt exits, write/fsync/replace
faults and post-commit uncertainty, Unicode paths, recovery and UI cancel/failure paths.
GUI dialogs use controlled replies; native macOS dialog/filesystem acceptance is P2.md.

Build with requirements-build.txt, then from repository root:

```sh
python -m pip wheel --no-deps --no-build-isolation --no-index --wheel-dir dist .
python -c "from setuptools.build_meta import build_sdist; build_sdist('dist')"
```

Example: examples/p2_two_members.strd. A2 JSON example/CLI remains supported separately;
it is not a P2 project file. No legacy dependency installation required.

## P2 macOS path-alias verification correction (2026-10-26)

PO evidence: macOS Python 3.12.2 / Tk8.6.13 aqua, original source112 tests with two
failures; GUI25 tests all PASS. That native GUI result remains accepted evidence.
The failures compared lexical temporary paths with canonical paths: the primary-replace
injection missed its target, and Save As expected the uncanonicalized spelling.
Tests now identify the canonical target independently and verify actual primary injection,
backup bytes, original bytes, unchanged save token and dirty state. Alias regressions cover
shared locking, stale writers, recovery and two real processes using different spellings.
Production code, schema, wheel0.4.0 and GUI are unchanged. No assertion is skipped.

Minimal native re-verification from the already-corrected P2 repository:

```sh
.venv-p1/bin/python scripts/run_tests.py --source
```

Expected115 tests PASS. No wheel reinstall or repeat of the accepted native GUI25 is
required for this test/document-only correction. Work Linux/alias results do not claim
native macOS acceptance. Other P2 PO acceptance gates retain their actual completion state.

---

# Historical P1 verification record

A1 and A2 are PO accepted. Historical statuses below describe their delivery dates.
From repository root, with Python/Tk available and a desktop display for GUI tests:

```sh
python3 scripts/run_tests.py --source
python3 scripts/run_gui_tests.py --source
python3 scripts/verify_distribution.py /PATH/strd_engine-0.3.0-py3-none-any.whl --gui
```

Headless suite: 87 methods (72 accepted + 15 P1 draft/freshness/adapter tests).
Real-widget suite: 12 methods. `--gui` checks the installed wheel in a clean venv
outside the repository, including entry-point metadata. Without `--gui` the
headless distribution gate remains usable without Tk/display. GUI failure to
initialize is reported NOT EXECUTED with nonzero exit, never a passing skip.

For an already installed pilot: `.venv-p1/bin/python scripts/run_tests.py` and
`.venv-p1/bin/python scripts/run_gui_tests.py`. Do not add `--source` to an installed
verification. macOS native gates remain in P1.md; Linux Tk evidence is not macOS proof.
Build with requirements-build.txt and the existing commands below, using version 0.3.0.

---

# Historical A2 verification record

A1 is PO accepted at 8017af4. Historical A1 evidence below is retained;
its old pending-acceptance statements do not override current PO decisions.

From repository root:

```sh
python3 -m venv --without-pip .venv-a2-source
.venv-a2-source/bin/python scripts/run_tests.py --source
python3 verification/a2_reference_calculations.py
python3 -m venv .venv-a2
.venv-a2/bin/python -m pip install --no-index --no-deps PATH_TO/strd_engine-0.2.0-py3-none-any.whl
.venv-a2/bin/python scripts/run_tests.py
.venv-a2/bin/python -m strd.assessment examples/a2_member.json
.venv-a2/bin/python scripts/verify_distribution.py PATH_TO/strd_engine-0.2.0-py3-none-any.whl
```

Windows: use the environment's Scripts/python.exe. Work runtime remains Linux
CPython 3.12.14; native macOS/Windows A2 results are not inferred. Source tests include
accepted 55 methods plus A2 source/unit/independent calculation, coverage, cases,
faults, provenance and compatibility checks. Actual totals/logs are in the handoff.
Fresh installed verification checks exact JSON resource bytes and runs all tests,
legacy smoke commands, independent worksheet and A2 sample from outside repository.

Build with pinned requirements-build.txt, then:

```sh
python -m pip wheel --no-deps --no-build-isolation --no-index --wheel-dir dist .
python -c "from setuptools.build_meta import build_sdist; build_sdist('dist')"
python scripts/verify_distribution.py dist/strd_engine-0.2.0-py3-none-any.whl
```

The wheel has no runtime dependency. sdist includes examples and verification.
Original PDFs are not needed to execute tests; manual source audit uses the supplied
PDFs and source hashes in A2_DATA.md. Golden response tests remain compatibility
evidence; independent book/Decimal cases remain engineering numerical evidence.

---

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
