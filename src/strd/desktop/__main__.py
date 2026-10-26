"""Launch the offline STRD desktop pilot: python -m strd.desktop."""
import sys


def main():
    try:
        import tkinter as tk
        from .ui import StrengthApp
        root = tk.Tk()
    except (ImportError, RuntimeError) as exc:
        print('STRD cannot start Tk. Use a Python installation with Tcl/Tk support.\n' + str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        # TclError when no display is available: fail visibly, never a silent launch.
        print('STRD could not open a desktop window.\n' + str(exc), file=sys.stderr)
        return 2
    StrengthApp(root)
    root.mainloop()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
