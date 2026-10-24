# STRD — steel design engineering proof

MS-1 adds a bounded, headless major-axis bending proof for the continuously braced H450x200x9x14 example in the supplied DPT manual. See [documentation](docs/README.md), [supported scope](docs/MS1.md), [reference evidence](docs/REFERENCE_PROOF.md) and [setup/tests](docs/TESTING.md).

From repository root, with Python 3.10+:

```sh
python -m unittest discover -s tests_verified -v
python -m strd_verified
```

The proof uses only Python's standard library. It is not a general beam checker or current-code certification. Shear, discrete bracing/LTB, other sections, analysis and UI are deferred. PASS applies only to the documented bending check.

## Legacy reference (unverified outside explicit proof)

Original scripts/catalogs remain unchanged; known defects are documented in MS-0. The historical installation instructions below apply to legacy work, NOT the MS-1 source-tree proof. Installing dependencies does not verify legacy calculations.

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
