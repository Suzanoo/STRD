# P1 desktop pilot (submitted for acceptance)

Install the delivered strd-engine 0.3.0 wheel in a fresh `.venv-p1`, then run
`.venv-p1/bin/python -m strd.desktop`. Python with Tk is required for the desktop.
See [P1 setup and use](docs/P1.md), [verification](docs/TESTING.md) and
[contracts](docs/COLLABORATION.md). Desktop/macOS is the PO-selected pilot.
The accepted A2 engineering engine and two verified SYS sections remain unchanged.

The following A2 instructions are historical; use P1 versions/commands above.

# STRD — bounded steel strength engine

MS0/MS1/MS2/A1 accepted. A2 submitted for PO review: two curated SYS rolled-H
sections and headless member/case/segment assessment under the accepted DPT book.
No UI, project persistence, force generation or additional design limit states.

```sh
python scripts/run_tests.py --source
```

After wheel installation:

```python
from strd.catalog import catalog_snapshot
from strd.assessment import assess_member
inventory = catalog_snapshot()
# result = assess_member(request_dictionary)
```

```sh
python -m strd.assessment examples/a2_member.json
```

The sample has two segments and two independently supplied ASD/LRFD cases. It is
not a load-combination generator. CHECKS_PASS is conditional flexure/shear success,
not whole-member acceptance; read coverage, each check and not_checked together.

Existing `strd` and `strd_verified` four-function APIs retain the fixed DPT book
fixture and accepted response contract. Manufacturer data does not replace it.

Read [docs](docs/README.md), [A2/API](docs/A2.md), [provenance](docs/A2_DATA.md),
[testing](docs/TESTING.md) and [roadmap proposals](docs/ROADMAP_REVIEW.md).
Python 3.10+ syntax, stdlib-only runtime; Work verification on Linux CPython 3.12.14.
Native acceptance and public release are separate gates. Source layout requires
installation for normal imports; tests have explicit --source mode.
Legacy is archived and excluded from wheels. Full source books/catalogs are not
redistributed; no new license grant or structural-design certification is implied.
