"""Run installed-package verification, or explicitly opt into --source testing."""
import argparse
from pathlib import Path
import sys
import unittest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root))  # Independent worksheet, not src.
    if args.source:sys.path.insert(0,str(root/'src'))
    import strd, strd_verified
    if not args.source:
        for module in (strd,strd_verified):
            if (root/'src').resolve() in Path(module.__file__).resolve().parents:
                parser.error('Source/editable import in installed verification; use a clean wheel environment.')
    print('Mode:', 'source' if args.source else 'installed', 'strd:', strd.__file__,flush=True)
    suite=unittest.defaultTestLoader.discover(str(root/'tests_verified'))
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
