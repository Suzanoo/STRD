# Reproducible verified-engine tests

Run from the STRD repository root after overlaying the complete changed files on the accepted baseline. Source-tree execution; Python 3.10+ syntax, standard library only. No pip downloads, conda, numpy/pandas or legacy setup.py required. Do not apply the ZIP as a standalone repository: the baseline legacy file is needed for the isolated regression probe.

## macOS/Linux

```sh
python3 -m venv --without-pip .venv-ms2
.venv-ms2/bin/python -m unittest discover -s tests_verified -v
.venv-ms2/bin/python -m strd_verified
.venv-ms2/bin/python -m strd_verified.ms2_examples
.venv-ms2/bin/python verification/ms2_reference_calculations.py
```

## Windows PowerShell

```powershell
py -3 -m venv --without-pip .venv-ms2
.\.venv-ms2\Scripts\python.exe -m unittest discover -s tests_verified -v
.\.venv-ms2\Scripts\python.exe -m strd_verified
.\.venv-ms2\Scripts\python.exe -m strd_verified.ms2_examples
.\.venv-ms2\Scripts\python.exe verification\ms2_reference_calculations.py
```

Use a fresh, task-specific environment location; preserve any existing user environments. `--without-pip` demonstrates no third-party dependency. Existing compatible environments may also run the commands.

## Coverage and evidence

- `tests_verified/test_bending.py`: all 21 accepted MS-1 tests unchanged. Running these alongside MS-2 is regression protection, not a repeated PO acceptance request.
- `tests_verified/test_h_beam.py`: 25 MS-2 test methods with parameterized subtests. Covers independent examples, LTB regions/exact adjacent-float boundaries, yielding cap, Cb/provenance, compactness, all shear equation regions/boundaries, factors, units, invalid/missing/nonfinite/overflow inputs, source faults, 6.2.2 exemption, deterministic fresh results, no calculation I/O and trace/exclusions.
- `verification/ms2_reference_calculations.py`: independent 50-digit Decimal worksheet with book literals and no production imports. Tests use numerical comparisons and analytical expectations, not smoke snapshots as their sole oracle.
- `python -m strd_verified`: original two MS-1 JSON results, unchanged.
- `python -m strd_verified.ms2_examples`: six MS-2 strength results (three examples x ASD/LRFD) plus the separately labeled unrounded Cb result. It prints JSON only; no product Save/Open or UI is implemented.

Actual implementation verification: Linux, CPython 3.12.14; fresh venv without pip; **46 tests PASS**, 0 skips, 0 failures. Both smoke commands and independent worksheet exit 0 with valid finite JSON. Exact logs are in the delivery. Python 3.10/3.11 and native Windows/macOS MS-2 execution are not claimed. Accepted MS-1 macOS evidence remains valid.

Private-kernel synthetic sections exercise shear buckling/classification branches; they are not additional supported catalog records. Reproducing the legacy short-Lb failure using AST avoids legacy numpy dependencies. Legacy files are not modified, and the test suite does not certify all legacy scripts. Text source reads use explicit UTF-8.

Run all `tests_verified` after scoped changes. Automated checks, artifact application verification, Coordinator review and PO acceptance are distinct. Native Desktop UI acceptance is inapplicable to this headless milestone. No production-design certification is implied.
