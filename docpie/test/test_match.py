import unittest
import logging

from docpie import bashlog
from docpie.element import Option, Command, Argument
from docpie.token import Argv

logger = logging.getLogger('docpie.test.match')


class MatchTest(unittest.TestCase):

    def true(self, expr):
        self.assertTrue(expr)

    def false(self, expr):
        self.assertFalse(expr)

    def argv(self, value):
        return Argv(value, True, True, True, True)

    def test_option(self):
        self.true(
            Option('-a').match(self.argv(['-a']), [], False))
        self.false(
            Option('-a').match(self.argv(['--alter']), [], False))
#         self.true(Option('-a', '--alter').match(Argv(['--alter'])))
#         self.true(Option('-').match(Argv(['-'])))
#         self.true(Option('--').match(Argv(['--'])))

#     def test_option_after_dashes(self):
#         tk = Argv(['--', '-a'])
#         tk.next()
#         self.false(Option('-a').match(tk))

#         tk = Argv(['--', '-aft'])
#         tk.next()
#         self.false(Option('-a').match(tk))
#         tk.next()
#         tk.putback('-ft')
#         self.false(Option('-f').match(tk))
#         tk.next()
#         tk.putback('-t')
#         self.false(Option('-t').match(tk))

#     def test_option_with_eq(self):
#         tk = Argv(['-a=value'])
#         self.true(Option('-a').match(tk))
#         self.assertEqual(tk.next(), ('value', (Argument,)))

#         tk = Argv(['-abc=value'])
#         self.true(Option('-a').match(tk))
#         self.true(Option('-b').match(tk))
#         self.true(Option('-c').match(tk))
#         self.assertEqual(tk.next(), ('value', (Argument,)))

#         tk = Argv(['-a='])
#         self.true(Option('-a').match(tk))
#         self.assertEqual(tk.next(), ('', (Argument,)))

#         tk = Argv(['--long='])
#         self.true(Option('--long').match(tk))
#         self.assertEqual(tk.next(), ('', (Argument,)))

#     def test_option_repeat(self):
#         tk = Argv(['-aa'])
#         opt = Option('-a')
#         self.true(opt.match(tk))
#         self.false(opt.match(tk))
#         self.true(opt.match(tk, repeat=True))

#         tk = Argv(['-t', '--test=sth'])
#         opt = Option('--test', '-t')
#         self.true(opt.match(tk))
#         self.false(opt.match(tk))
#         self.true(opt.match(tk, repeat=True))

#     def test_option_long_broken(self):
#         tk = Argv(['--sth=--value'])
#         self.true(Option('-s', '--sth').match(tk))
#         self.assertEqual(tk.current(), ('--value', (Argument, )))
#         self.false(Option('--value').match(tk))
#         self.true(tk.broken)

#     def test_cmd(self):
#         self.true(Command('test').match(Argv(['test'])))
#         self.false(Command('').match(Argv(['-'])))

#     def test_cmd_repeat(self):
#         tk = Argv(['cmd', 'cmd'])
#         cmd = Command('cmd')
#         self.true(cmd.match(tk))
#         self.false(cmd.match(tk))
#         self.true(cmd.match(tk, repeat=True))

#     def test_cmd_broken(self):
#         tk = Argv(['--test=any'])
#         self.true(Option('--test').match(tk))

#         self.false(Command('any').match(tk))
#         self.true(tk.broken)

#         tk = Argv(['any'])
#         tk.broken = True
#         self.false(Command('any').match(tk))

#     def test_nonstd_cmd(self):
#         self.true(Command('--test~=here').match(Argv(['--test~=here'])))
#         self.false(Command('here').match(Argv(['here=go'])))

#     def test_arg(self):
#         self.true(Argument('<test>').match(Argv(['test'])))
#         tk = Argv(['any'])
#         tk.broken = True
#         self.false(Argument('<any>').match(tk))

#     def test_arg_repeat(self):
#         tk = Argv(['any', 'any'])
#         arg = Argument('<any>')
#         self.true(arg.match(tk))
#         self.false(arg.match(tk))
#         self.true(arg.match(tk, repeat=True))
#         self.assertIsNone(tk.current()[0])


def suite():
    return unittest.TestSuite(case())

    # return unittest.TestSuite()


def case():
    return (
            unittest.TestLoader().loadTestsFromTestCase(MatchTest),
        )


if __name__ == '__main__':
    bashlog.stdoutlogger('docpie', bashlog.DEBUG, True)
    unittest.TextTestRunner().run(suite())
