"""JSON assessment entry point: python -m strd.assessment input.json (or - for stdin)."""
import argparse
import json
from pathlib import Path
import sys
from . import assess_member


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field: ' + key)
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='UTF-8 JSON filename or - for stdin')
    args = parser.parse_args()
    try:
        text = sys.stdin.read() if args.input == '-' else Path(args.input).read_text(encoding='utf-8')
        request = json.loads(text, object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({'status': 'INVALID_INPUT', 'message': str(exc)}))
        return 2
    result = assess_member(request)
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 0 if result['status'] == 'CHECKS_PASS' else (1 if result['status'] == 'CHECKS_FAIL' else 2)

if __name__ == '__main__':
    raise SystemExit(main())
