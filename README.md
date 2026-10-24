# STRD — bounded steel strength checks

The verified source package supports the book-based H450x200x9x14 fixture:
major-axis bending with yielding/LTB, and unstiffened web shear, ASD/LRFD.
MS-1 is accepted. MS-2 is implemented and submitted for review; MS-3 is not authorized.
See [documentation](docs/README.md), [MS-2 applicability/API](docs/MS2.md),
[reference evidence](docs/MS2_REFERENCE.md), and [setup/tests](docs/TESTING.md).

From repository root, Python 3.10+ (standard library only):

```sh
python -m unittest discover -s tests_verified -v
python -m strd_verified.ms2_examples
python verification/ms2_reference_calculations.py
```

The accepted MS-1 API `check_bending` and `python -m strd_verified` remain unchanged.
The new APIs are `check_flexure`, `check_web_shear` and `moment_gradient_factor`.
One verified section/material record is supported, not the legacy catalog.
PASS applies only to the specified individual check and asserted assumptions;
no whole-member, bracing-system, current-code or production certification is implied.
Analysis, combined actions, UI and project Save/Open remain excluded.

## Legacy reference (unverified outside explicit proof)

Original scripts/catalogs remain unchanged; known defects are documented in MS-0. The historical installation instructions below apply to legacy work, NOT the verified source-tree package. Installing dependencies does not verify legacy calculations.

### Tools

1. Install Python, Git, Anaconda

- [Python](https://www.python.org/downloads/)
- [Git](https://github.com/git-guides/install-git)
- [Anaconda](https://docs.anaconda.com/anaconda/install/index.html)

2. Create project folder
3. Clone this Repository
4. Create Conda env then activate it
5. Install dependency
6. Enjoy

```
mkdir dev
cd dev
git clone https://github.com/Suzanoo/STRD.git
conda create --name <Conda env name> python=3.10
conda activate <Conda env name>
python setup.py install
```
