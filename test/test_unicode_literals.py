from __future__ import unicode_literals

import io
import os
import re
import unittest

rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IGNORED_FILES = [
    'setup.py',  # http://bugs.python.org/issue13943
]


class TestUnicodeLiterals(unittest.TestCase):
    def test_all_files(self):
        print('Skipping this test (not yet fully implemented)')
        return

        for dirpath, _, filenames in os.walk(rootDir):
            for basename in filenames:
                if not basename.endswith('.py'):
                    continue
                if basename in IGNORED_FILES:
                    continue

                fn = os.path.join(dirpath, basename)
                with io.open(fn, encoding='utf-8') as inf:
                    code = inf.read()

                if "'" not in code and '"' not in code:
                    continue
                imps = 'from __future__ import unicode_literals'
                self.assertTrue(
                    imps in code,
                    ' %s  missing in %s' % (imps, fn))

                m = re.search(r'(?<=\s)u[\'"](?!\)|,|$)', code)
                if m is not None:
                    self.assertTrue(
                        m is None,
                        'u present in %s, around %s' % (
                            fn, code[m.start() - 10:m.end() + 10]))


if __name__ == '__main__':
    unittest.main()
