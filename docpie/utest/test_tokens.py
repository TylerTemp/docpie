import unittest
import logging
from docpie.tokens import Argv
logger = logging.getLogger('docpie.test.tokens')


class ArgvTest(unittest.TestCase):

    def test_insert(self):
        a = self.argv()
        a.insert(0, '-a')
        self.ck(a, [], False)

        a = self.argv()
        a.insert(0, 'a')
        self.ck(a, ['a'], True)

        a = self.argv()
        a.insert(0, '--pie')
        # won't check long options so far
        self.ck(a, ['--pie'], True)

    def test_insert_dashes(self):
        a = self.argv(known=['-a'])
        a.insert(0, '-a')
        self.ck(a, ['-a'], True)

        a = self.argv(['--'], known=['-a'])
        a.insert(0, '-a')
        self.ck(a, ['-a', '--'], True)

        a = self.argv(['--'], known=['-a'])
        a.insert(0, '-b')
        self.ck(a, ['--'], False)

        a = self.argv(['--'], known=['-a'])
        a.insert(1, '-b')
        self.ck(a, ['--', '-b'], True)

    def test_insert_none_autodashes(self):
        a = self.argv(['--'], auto2dashes=False, known=['-a'])
        a.insert(0, '-a')
        self.ck(a, ['-a', '--'], True)

        a = self.argv(['--'], auto2dashes=False, known=['-a'])
        a.insert(0, '-b')
        self.ck(a, ['--'], False)

        a = self.argv(['--'], auto2dashes=False, known=['-a'])
        a.insert(1, '-b')
        self.ck(a, ['--'], False)

    def ck(self, argv, content=[], none=False):
        self.assertEqual(list(argv), content)
        if none:
            self.assertIsNone(argv.error)
        else:
            self.assertIsNotNone(argv.error)

    def argv(self, argv=None, auto2dashes=True, stdopt=True, attachopt=True,
             attachvalue=True, known=None):

        if argv is None:
            argv = []
        if known is None:
            known = []

        return Argv(argv, auto2dashes, stdopt, attachopt, attachvalue, known)


def case():
    return (unittest.TestLoader().loadTestsFromTestCase(ArgvTest),)


def suite():
    return unittest.TestSuite(case())


def main():
    unittest.TextTestRunner().run(suite())


if __name__ == '__main__':
    # bashlog.stdoutlogger(None, bashlog.DEBUG, True)
    unittest.main()