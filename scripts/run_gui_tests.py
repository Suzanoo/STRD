"""Real Tk widget verification; requires macOS/Windows desktop or Linux display."""
import argparse
from pathlib import Path
import sys
import unittest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',action='store_true');args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    if args.source:sys.path.insert(0,str(root/'src'))
    import strd.desktop
    if not args.source and (root/'src').resolve() in Path(strd.desktop.__file__).resolve().parents:
        p.error('Use a clean installed wheel, or explicit --source mode.')
    try:
        import tkinter as tk
        probe=tk.Tk();print('Actual GUI runtime:',sys.version,'Tk',probe.tk.call('package','require','Tk'),probe.tk.call('tk','windowingsystem'),flush=True);probe.destroy()
    except Exception as exc:
        print('GUI verification NOT EXECUTED: '+str(exc),file=sys.stderr);return 2
    tests=unittest.defaultTestLoader.discover(str(root/'tests_desktop'))
    return 0 if unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
