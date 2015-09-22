import unittest
import logging

from docpie import bashlog
from docpie.element import Option, Argument, Command
from docpie.token import Token

logger = logging.getLogger('docpie.test.element')


class TokenTest(unittest.TestCase):
    def eq(self, *a, **k):
        return self.assertEqual(*a, **k)

    def setUp(self):
        self.l = ['[', '(', ')', ']']

    @property
    def t(self):
        return Token(self.l)

    def test_next(self):
        t = self.t
        for each in self.l:
            self.eq(each, t.current())
            self.eq(each, t.next())

        if hasattr(self, 'assertIsNone'):
            none = self.assertIsNone
        else:
            def none(expr, msg=None):
                assert expr is None, msg
        none(t.next())
        none(t.current())

    def test_bracket_level0(self):
        t = self.t
        start = t.next()
        self.eq(t.till_end_bracket(start), ['(', ')'])

    def test_bracket_level1(self):
        t = self.t
        t.next()
        start = t.next()
        self.eq(t.till_end_bracket(start), [])


def suite():
    return unittest.TestSuite(case())


def case():
    return (
            unittest.TestLoader().loadTestsFromTestCase(TokenTest),
    )


def main():
    unittest.TextTestRunner().run(suite())

if __name__ == '__main__':
    # bashlog.getlogger('docpie', bashlog.DEBUG, True)
    main()
