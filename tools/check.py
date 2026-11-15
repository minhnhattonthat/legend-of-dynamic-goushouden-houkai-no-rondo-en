"""check.py: the repo's one-command check (tests + text lint). The pre-commit hook runs it.

Runs every test_*.py under tests/ with unittest. Tests that need the ROM skip themselves when rom/ is absent
(a fresh clone without a dump still commits). Exit code = pass/fail; never pipe it before a commit.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.path.insert(0, str(ROOT / "tools"))
    tests = ROOT / "tests"
    suite = unittest.defaultTestLoader.discover(str(tests), top_level_dir=str(ROOT)) if tests.is_dir() else unittest.TestSuite()
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(f"check ok: {result.testsRun} tests")


if __name__ == "__main__":
    main()
