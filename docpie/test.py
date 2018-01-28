# coding: utf-8
import unittest
import logging
import sys
import platform

from docpie import docpie, Docpie
from docpie.error import DocpieExit, \
                         UnknownOptionExit, \
                         ExceptNoArgumentExit, \
                         ExpectArgumentExit, \
                         ExpectArgumentHitDoubleDashesExit, \
                         AmbiguousPrefixExit
import json

try:
    from io import StringIO
except ImportError:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

logger = logging.getLogger('docpie.test.docpie')


class BasicTest(unittest.TestCase):

    def test_commands(self):
        eq = self.assertEqual
        eq(docpie('Usage: prog add', 'prog add'),
           {'add': True, '--': False})
        eq(docpie('Usage: prog [add]', 'prog'),
           {'add': False, '--': False})
        eq(docpie('Usage: prog [add]', 'prog add'),
           {'add': True, '--': False})
        eq(docpie('Usage: prog (add|rm)', 'prog add'),
           {'add': True, 'rm': False, '--': False})
        eq(docpie('Usage: prog (add|rm)', 'prog rm'),
           {'add': False, 'rm': True, '--': False})
        eq(docpie('Usage: prog a b', 'prog a b'),
           {'a': True, 'b': True, '--': False})
        self.assertRaises(DocpieExit, docpie, 'Usage: prog a b', 'b a')

    def test_docpie(self):
        eq = self.assertEqual

        doc = '''Usage: prog [-v] A

                 Options: -v  Be verbose.'''

        eq(docpie(doc, 'prog arg'), {'-v': False, 'A': 'arg',
                                     '--': False})
        eq(docpie(doc, 'prog -v arg'), {'-v': True, 'A': 'arg',
                                        '--': False})

        doc = '''
        Usage: prog [-vqr] [FILE]
               prog INPUT OUTPUT
               prog --help

        Options:
          -v  print status messages
          -q  report only file names
          -r  show all occurrences of the same error
          --help

        '''
        a = docpie(doc, 'prog -vqr file.py')
        eq(a, {'-v': True, '-q': True, '-r': True, '--help': False,
               'FILE': 'file.py', 'INPUT': None, 'OUTPUT': None,
               '--': False})

        eq(docpie(doc, 'prog -v'),
           {'-v': True, '-q': False, '-r': False, '--help': False,
            'FILE': None, 'INPUT': None, 'OUTPUT': None,
            '--': False})
        #
        self.assertRaises(DocpieExit, docpie, doc,
                          'prog -v input.py output.py')
        self.assertRaises(DocpieExit, docpie, doc, 'prog --fake')
        # --hel -> --help
        with StdoutRedirect():
            self.assertRaises(SystemExit, docpie, doc, 'prog --hel')

    def test_command_help(self):

        doc = 'usage: prog --help-commands | --help'
        with StdoutRedirect():
            self.assertRaises(SystemExit, docpie, doc, 'prog --help')

    # this syntax won't work on python 3.2
    def test_unicode(self):
        try:
            self.assertEqual(
                docpie(eval("u'usage: prog [-o <呵呵>]'"),
                       eval("u'prog -o 嘿嘿'")),
                {'-o': True, eval("u'<呵呵>'"): eval("u'嘿嘿'"), '--': False})
        except SyntaxError:
            sys.stdout.write('skip test_unicode')
            sys.stdout.flush()

    def test_count_multiple_flags(self):
        eq = self.assertEqual
        eq(docpie('usage: prog [-vv]', 'prog'),
           {'-v': 0, '--': False})
        eq(docpie('usage: prog [-v]', 'prog -v'),
           {'-v': True, '--': False})
        self.assertRaises(DocpieExit, docpie, 'usage: prog [(-vv)]', 'prog -v')
        eq(docpie('usage: prog [-vv]', 'prog -v'), {'-v': 1, '--': False})
        eq(docpie('usage: prog [-vv]', 'prog -vv'),
           {'-v': 2, '--': False})
        # New in 0.0.9
        eq(docpie('usage: prog [-v | -vv | -vvv]', 'prog -vvv'),
           {'-v': 3, '--': False})
        eq(docpie('usage: prog [-vvv | -vv | -v]', 'prog -vvv'),
           {'-v': 3, '--': False})
        eq(docpie('usage: prog -v...', 'prog -vvvvvv'),
           {'-v': 6, '--': False})
        eq(docpie('usage: prog [--ver --ver]', 'prog --ver --ver'),
           {'--ver': 2, '--': False})
        self.assertRaises(DocpieExit, docpie,
                          'usage: prog [-vv]', 'prog -vvv')

    def test_any_options_parameter(self):
        self.assertRaises(
            DocpieExit, docpie,
            'usage: prog [options]', 'prog -foo --bar --spam=eggs')
        self.assertRaises(
            DocpieExit, docpie,
            'usage: prog [options]', 'prog --foo --bar --bar')
        self.assertRaises(
            DocpieExit, docpie,
            'usage: prog [options]', 'prog --long=arg --long=another')

    def test_default_value_for_positional_arguments(self):
        eq = self.assertEqual

        doc = '''Usage: prog [--data=<data>...]\n
                 Options:\n\t-d --data=<arg>...    Input data [default: x]
              '''
        eq(docpie(doc, 'prog'), {'--data': ['x'], '-d': ['x'],
                                 '--': False})

        doc = '''Usage: prog [--data=<data>...]\n
                 Options:\n\t-d --data=<arg>...    Input data [default: x y]
              '''
        eq(docpie(doc, 'prog'), {'--data': ['x', 'y'], '-d': ['x', 'y'],
                                 '--': False})

        doc = '''Usage: prog [--data=<data>...]\n
                 Options:\n\t-d --data=<arg>...    Input data [default: x y]
              '''
        eq(docpie(doc, 'prog --data=this'),
           {'--data': ['this'], '-d': ['this'], '--': False})

    def test_fix_this(self):
        eq = self.assertEqual
        # this now works:
        eq(docpie('usage: prog --long=<a>', 'prog --long='),
           {'--long': '', '--': False})
        # this will work:
        doc = '''
        Usage: prog --long=<a>

        Options:
            --long=<a>    it requires a value'''
        eq(docpie(doc, 'prog --long='), {'--long': '',
                                         '--': False})

        eq(docpie('usage: prog -l <a>\n\n'
                  'options: -l <a>', ['prog', '-l', '']),
           {'-l': '', '--': False})

    # no this feature so far
    def test_options_first(self):
        eq = self.assertEqual
        eq(docpie('usage: prog [--opt] [<args>...]', 'prog --opt this that'),
           {'--opt': True, '<args>': ['this', 'that'],
            '--': False})

        eq(docpie('usage: prog [--opt] [<args>...]',
                  'prog this that --opt'),
           {'--opt': True, '<args>': ['this', 'that'],
            '--': False})
        # assert docpie('usage: prog [--opt] [<args>...]',
        #               'prog this that --opt') == {'--opt': False,
        #                             '<args>': ['this', 'that', '--opt']}

    def test_options_shortcut_does_not_include_options_in_usage_pattern(self):
        true = self.assertTrue
        false = self.assertFalse
        args = docpie('''usage: prog [-a] [-b] [options]


                      options:
                        -x
                        -y''',
                      'prog -ax')

        true(args['-a'])
        false(args['-b'])
        true(args['-x'])
        false(args['-y'])

    def test_issue_docopt_65_evaluate_argv_when_called_not_when_imported(self):
        eq = self.assertEqual

        sys.argv = 'prog -a'.split()
        eq(docpie('usage: prog [-a][-b]'),
           {'-a': True, '-b': False, '--': False})

        sys.argv = 'prog -b'.split()
        eq(docpie('usage: prog [-a][-b]'),
           {'-a': False, '-b': True, '--': False})

    def test_issue_71_double_dash_is_not_a_valid_option_argument(self):
        doc = '''Usage:
                    fubar [-f LEVEL] [--] <items>...

                 Options:
                   -f LEVEL'''

        self.assertRaises(DocpieExit, docpie, doc, 'fubar -f -- 1 2 ')

    def test_new_doc_format(self):
        true = self.assertTrue
        false = self.assertFalse
        doc = '''
    Usage:
        prog [options]

    Options:
        -a
            description of -a
        -b  a long long long long long long long
            long long long long long long long long
            description of -b'''

        args = docpie(doc, 'prog -a -b'.split())
        true(args['-a'])
        true(args['-b'])


class RunDefaultTest(unittest.TestCase):

    def eq(self, doc, result, argv=None):
        self.assertEqual(docpie(doc, argv), result)

    def fail(self, doc, argv=None, exception=DocpieExit):
        self.assertRaises(exception, docpie, doc, argv)

    def test_empty(self):
        doc = '''Usage: prog'''

        sys.argv = ['prog']
        self.eq(doc, {'--': False})

        sys.argv = ['prog', '-xxx']
        self.fail(doc)

    def test_one_option_short(self):
        doc = '''Usage: prog [options]

Options: -a  All.
'''

        sys.argv = ['prog']
        self.eq(doc, {'-a': False, '--': False})

        sys.argv = ['prog', '-a']
        self.eq(doc, {'-a': True, '--': False})

        sys.argv = ['prog', '-x']
        self.fail(doc)

    def test_one_option_long(self):
        doc = '''Usage: prog [options]

Options: --all  All.

'''
        sys.argv = ['prog']
        self.eq(doc, {'--all': False, '--': False})

        sys.argv = ['prog', '--all']
        self.eq(doc, {'--all': True, '--': False})

        sys.argv = ['prog', '--xxx']
        self.fail(doc)

    def test_one_option_alias(self):
        doc = '''Usage: prog [options]

        Options: -v, --verbose  Verbose.
        '''
        sys.argv = ['prog', '--verbose']
        self.eq(doc, {'-v': True, '--verbose': True, '--': False})

        # Support since 0.0.7
        sys.argv = ['prog', '--ver']
        self.eq(doc, {'-v': True, '--verbose': True, '--': False})

        doc = '''Usage: prog [options]

        Options: --verbose  Verbose.
                 --version  print version
        '''
        sys.argv = ['prog', '--ver']  # --version? --verbose?
        self.assertRaises(DocpieExit, docpie, doc, version='sth')

        # But you can do this:
        doc = '''Usage: prog [options]

Options: -v, --ver, --verbose  Verbose.
'''
        sys.argv = ['prog', '--ver']
        self.eq(doc, {'-v': True, '--ver': True, '--verbose': True,
                      '--': False})

    def test_attached_value_short_opt(self):
        doc = '''Usage: prog [options]

Options: -p PATH
'''

        sys.argv = ['prog', '-p', 'home/']
        self.eq(doc, {'-p': 'home/', '--': False})

        sys.argv = ['prog', '-phome/']
        self.eq(doc, {'-p': 'home/', '--': False})

        sys.argv = ['prog', '-p']
        self.fail(doc)

    def test_equal_value_long_opt(self):
        doc = '''Usage: prog [options]

Options: --path <path>
'''

        sys.argv = ['prog', '--path', 'home/']
        self.eq(doc, {'--path': 'home/', '--': False})

        sys.argv = ['prog', '--path=home/']
        self.eq(doc, {'--path': 'home/', '--': False})

        # Note: same from docopt since 0.0.7
        sys.argv = ['prog', '--pa=home/']
        self.eq(doc, {'--path': 'home/', '--': False})

        # Note: same from docopt since 0.0.7
        sys.argv = ['prog', '--pa', 'home/']
        self.eq(doc, {'--path': 'home/', '--': False})

        sys.argv = ['prog', '--path']
        self.fail(doc)

    def test_value_for_short_long_opt(self):
        expected = {'-p': 'root', '--path': 'root', '--': False}
        doc = '''Usage: prog [options]

Options: -p PATH, --path=<path>  Path to files.
'''

        sys.argv = ['prog', '-proot']
        self.eq(doc, expected)

        doc = '''Usage: prog [options]

Options: -p --path PATH  Path to files.
'''

        sys.argv = ['prog', '-p', 'root']
        self.eq(doc, expected)

        sys.argv = ['prog', '--path', 'root']
        self.eq(doc, expected)

    def test_opt_default(self):
        doc = '''Usage: prog [options]

Options:
 -p PATH  Path to files [default: ./]
'''
        sys.argv = ['prog']
        self.eq(doc, {'-p': './', '--': False})

        sys.argv = ['prog', '-phome']
        self.eq(doc, {'-p': 'home', '--': False})

        # Note: a little different from docpie
        doc = '''UsAgE: prog [options]

OpTiOnS: --path=<files>  Path to files
                         [dEfAuLt: /root]
'''

        sys.argv = ['prog']
        self.eq(doc, {'--path': '/root', '--': False})

        sys.argv = ['prog', '--path=home']
        self.eq(doc, {'--path': 'home', '--': False})

    def test_more_short_opt(self):
        doc = '''usage: prog [options]

options:
    -a        Add
    -r        Remote
    -m <msg>  Message
'''

        sys.argv = ['prog', '-a', '-r', '-m', 'hello']
        self.eq(doc, {'-a': True, '-r': True, '-m': 'hello',
                      '--': False})

        sys.argv = ['prog', '-ramsth']
        self.eq(doc, {'-a': True, '-r': True, '-m': 'sth',
                      '--': False})

        sys.argv = ['prog', '-a', '-r']
        self.eq(doc, {'-a': True, '-r': True, '-m': None,
                      '--': False})

    def test_furture_not_support_now(self):
        doc = '''Usage: prog [options]

Options: --version
         --verbose
'''

        sys.argv = ['prog', '--version']
        self.eq(doc, {'--version': True, '--verbose': False,
                      '--': False})

        sys.argv = ['prog', '--verbose']
        self.eq(doc, {'--version': False, '--verbose': True,
                      '--': False})

        sys.argv = ['prog', '--ver']
        self.fail(doc)

        # support since 0.0.7
        sys.argv = ['prog', '--verb']
        self.eq(doc, {'--version': False, '--verbose': True,
                      '--': False})

    def test_opt_format(self):
        doc = '''usage: prog [-a -r -m <msg>]

options:
 -a        Add
 -r        Remote
 -m <msg>  Message
'''

        sys.argv = ['prog', '-rammed']
        self.eq(doc, {'-a': True, '-r': True, '-m': 'med',
                      '--': False})

        # New in 0.1.1
        doc = '''usage: prog [-armMSG]

options: -a        Add
         -r        Remote
         -m <msg>  Message
'''
        self.eq(doc, {'--': False, '-a': True, '-m': 'med', '-r': True})

        doc = '''usage: prog [-arm MEG]

options: -a        Add
         -r        Remote
         -m <msg>  Message
'''
        sys.argv = sys.argv = ['prog', '-r', '-a', '-m', 'Hello']
        self.eq(doc, {'-a': True, '-r': True, '-m': 'Hello',
                      '--': False})

    def test_opt_no_shortcut(self):
        doc = '''usage: prog -a -b

options:
 -a
 -b
 '''

        sys.argv = ['prog', '-a', '-b']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-b', '-a']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-a']
        self.fail(doc)

        sys.argv = ['prog']
        self.fail(doc)

    def test_required_opt_unit(self):
        doc = '''usage: prog (-a -b)

options: -a
         -b
'''

        sys.argv = ['prog', '-a', '-b']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-b', '-a']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-a']
        self.fail(doc)

        sys.argv = ['prog']
        self.fail(doc)

    def test_optional_opt_in_usage(self):
        doc = '''usage: prog [-a] -b

options: -a
 -b
 '''

        sys.argv = ['prog', '-a', '-b']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-b', '-a']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-b']
        self.eq(doc, {'-a': False, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-a']
        self.fail(doc)

        sys.argv = ['prog']
        self.fail(doc)

    def test_required_unit_opt(self):
        doc = '''usage: prog [(-a -b)]

options: -a
         -b
'''

        sys.argv = ['prog', '-a', '-b']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-b', '-a']
        self.eq(doc, {'-a': True, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-b']
        self.fail(doc)

        sys.argv = ['prog', '-a']
        self.fail(doc)

        sys.argv = ['prog']
        self.eq(doc, {'-a': False, '-b': False,
                      '--': False})

    def test_required_either_opt(self):
        doc = '''usage: prog (-a|-b)

options: -a
         -b
'''
        sys.argv = ['prog', '-a', '-b']
        self.fail(doc)

        sys.argv = ['prog']
        self.fail(doc)

        sys.argv = ['prog', '-b']
        self.eq(doc, {'-a': False, '-b': True,
                      '--': False})

        sys.argv = ['prog', '-a']
        self.eq(doc, {'-a': True, '-b': False,
                      '--': False})

    def test_optional_either_opt(self):
        doc = '''usage: prog [ -a | -b ]

options: -a
         -b
'''

        sys.argv = ['prog', '-a', '-b']
        self.fail(doc)

        sys.argv = ['prog']
        self.eq(doc, {'-a': False, '-b': False,
                      '--': False})

        sys.argv = ['prog', '-a']
        self.eq(doc, {'-a': True, '-b': False,
                      '--': False})

        sys.argv = ['prog', '-b']
        self.eq(doc, {'-a': False, '-b': True,
                      '--': False})

    def test_one_arg(self):
        doc = '''usage: prog <arg>'''

        sys.argv = ['prog', '10']
        self.eq(doc, {'<arg>': '10', '--': False})

        sys.argv = ['prog', '10', '20']
        self.fail(doc)

        sys.argv = ['prog']
        self.fail(doc)

    def test_one_optional_arg(self):
        doc = '''usage: prog [<arg>]'''

        sys.argv = ['prog', '10']
        self.eq(doc, {'<arg>': '10', '--': False})

        sys.argv = ['prog', '10', '20']
        self.fail(doc)

        sys.argv = ['prog']
        self.eq(doc, {'<arg>': None, '--': False})

    def test_more_arg(self):
        doc = '''usage: prog <kind> <name> <type>'''

        sys.argv = ['prog', '10', '20', '40']
        self.eq(doc, {'<kind>': '10', '<name>': '20', '<type>': '40',
                      '--': False})

        sys.argv = ['prog', '10', '20']
        self.fail(doc)

        sys.argv = ['prog']
        self.fail(doc)

    def test_optional_group_arg(self):
        doc = '''usage: prog <kind> [<name> <type>]'''

        sys.argv = ['prog', '10', '20', '40']
        self.eq(doc, {'<kind>': '10', '<name>': '20', '<type>': '40',
                      '--': False})

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'<kind>': '10', '<name>': '20', '<type>': None,
                      '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'<kind>': '10', '<name>': None, '<type>': None,
                      '--': False})

        sys.argv = ['prog']
        self.fail(doc)

    def test_arg_in_branch_alias(self):
        doc = '''usage: prog [<name>|<pattern>]'''

        sys.argv = ['prog', 'docpie']
        self.eq(doc, {'<name>': 'docpie', '<pattern>': 'docpie',
                      '--': False})

    def test_arg_branch_unbalanced(self):
        doc = '''usage: prog [<kind> | <name> <type>]'''

        sys.argv = ['prog', '10', '20', '40']
        self.fail(doc)

        # fixed in 0.0.9
        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'<kind>': None, '<name>': '10', '<type>': '20',
                      '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'<kind>': '10', '<name>': None, '<type>': None,
                      '--': False})

        # But this works
        doc = '''usage: prog [<name> <type> | <kind>]'''
        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'<kind>': None, '<name>': '10', '<type>': '20',
                      '--': False})

        # This also works
        sys.argv = ['prog', '10']
        self.eq(doc, {'<kind>': '10', '<name>': None, '<type>': None,
                      '--': False})

    def test_unit_arg_opt_combo(self):
        doc = '''usage: prog (<kind> --all | <name>)

options:
 --all'''

        sys.argv = ['prog', '10', '--all']
        self.eq(doc, {'<kind>': '10', '<name>': None, '--all': True,
                      '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'<kind>': None, '<name>': '10', '--all': False,
                      '--': False})

        sys.argv = ['prog']
        self.fail(doc)

    def test_multi_arg(self):
        doc = '''usage: prog [<name> <name>]'''

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'<name>': ['10', '20'], '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'<name>': ['10'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'<name>': [], '--': False})

        # equal to
        doc = '''usage: prog [<name>] [<name>]'''
        sys.argv = ['prog', '10']
        self.eq(doc, {'<name>': ['10'], '--': False})

    def test_optinal_required_unit_arg(self):
        doc = '''usage: prog [(<name> <name>)]'''

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'<name>': ['10', '20'], '--': False})

        sys.argv = ['prog', '10']
        self.fail(doc)

        sys.argv = ['prog']
        self.eq(doc, {'<name>': [], '--': False})

    def test_repeat_required_arg(self):
        doc = '''usage: prog NAME...'''

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'NAME': ['10', '20'], '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'NAME': ['10'], '--': False})

        sys.argv = ['prog']
        self.fail(doc)

    def test_repeat_optional_arg(self):
        doc = '''usage: prog [NAME]...'''

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'NAME': ['10', '20'], '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'NAME': ['10'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'NAME': [], '--': False})

    def test_repeat_optional_arg_another_format(self):
        doc = '''usage: prog [NAME...]'''

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'NAME': ['10', '20'], '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'NAME': ['10'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'NAME': [], '--': False})

    def test_repeat_optional_arg_nested(self):
        doc = '''usage: prog [NAME [NAME ...]]'''

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'NAME': ['10', '20'], '--': False})

        sys.argv = ['prog', '10']
        self.eq(doc, {'NAME': ['10'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'NAME': [], '--': False})

    def test_branch_same_arg_dif_partner(self):
        doc = '''usage: prog (NAME | --foo NAME)

options: --foo
'''

        sys.argv = ['prog', '10']
        self.eq(doc, {'NAME': '10', '--foo': False, '--': False})

        sys.argv = ['prog', '--foo', '10']
        self.eq(doc, {'NAME': '10', '--foo': True, '--': False})

        sys.argv = ['prog', '--foo=10']
        self.fail(doc)

    def test_optional_and_required_unit(self):
        doc = '''usage: prog (NAME | --foo) [--bar | NAME]

options: --foo
         --bar'''

        sys.argv = ['prog', '10']
        self.eq(doc, {'NAME': ['10'], '--foo': False, '--bar': False,
                      '--': False})

        sys.argv = ['prog', '10', '20']
        self.eq(doc, {'NAME': ['10', '20'], '--foo': False, '--bar': False,
                      '--': False})

        sys.argv = ['prog', '--foo', '--bar']
        self.eq(doc, {'NAME': [], '--foo': True, '--bar': True,
                      '--': False})

    def test_example(self):
        doc = '''Naval Fate.

Usage:
  prog ship new <name>...
  prog ship [<name>] move <x> <y> [--speed=<kn>]
  prog ship shoot <x> <y>
  prog mine (set|remove) <x> <y> [--moored|--drifting]
  prog -h | --help
  prog --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Mored (anchored) mine.
  --drifting    Drifting mine.
'''

        sys.argv = ['prog', 'ship', 'Guardian', 'move',
                    '150', '300', '--speed=20']
        self.eq(doc, {'--drifting': False,
                      '--help': False,
                      '-h': False,
                      '--moored': False,
                      '--speed': '20',
                      '--version': False,
                      '--': False,
                      '<name>': ['Guardian'],
                      '<x>': '150',
                      '<y>': '300',
                      'mine': False,
                      'move': True,
                      'new': False,
                      'remove': False,
                      'set': False,
                      'ship': True,
                      'shoot': False})

    def test_one_long_opt_value(self):
        doc = '''usage: prog --hello'''

        sys.argv = ['prog', '--hello']
        self.eq(doc, {'--hello': True, '--': False})

        # Note: different form docopt:
        # You must tell docpie that `--hello` expects a value in `options:`
        # doc = '''usage: prog [--hello=<world>]'''
        doc = '''usage: prog [--hello=<world>]

Options:
    --hello=<world>'''

        sys.argv = ['prog']
        self.eq(doc, {'--hello': None, '--': False})

    def test_optional_opt(self):
        doc = '''usage: prog [-o]'''

        sys.argv = ['prog', '-o']
        self.eq(doc, {'-o': True, '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'-o': False, '--': False})

    def test_one_optional_short_opt(self):
        doc = '''Usage: prog [-o]'''

        sys.argv = ['prog', '-o']
        self.eq(doc, {'-o': True, '--': False})

    # Note: docpie does not have this future
    def test_either_option(self):
        doc = '''usage: prog --aabb | --aa'''

        sys.argv = ['prog', '--aa']
        self.eq(doc, {'--aabb': False, '--aa': True, '--': False})

        sys.argv = ['prog', '--a']
        self.fail(doc)

    def test_count_option(self):
        doc = '''usage: prog -v'''
        sys.argv = ['prog', '-v']
        self.eq(doc, {'-v': True, '--': False})

        doc = '''usage: prog [-v -v]'''
        sys.argv = ['prog']
        self.eq(doc, {'-v': 0, '--': False})
        sys.argv = ['prog', '-v']
        self.eq(doc, {'-v': 1, '--': False})
        sys.argv = ['prog', '-vv']
        self.eq(doc, {'-v': 2, '--': False})

        doc = '''usage: prog [(-v -v)]'''
        sys.argv = ['prog']
        self.eq(doc, {'-v': 0, '--': False})
        sys.argv = ['prog', '-v']
        self.fail(doc)
        sys.argv = ['prog', '-vv']
        self.eq(doc, {'-v': 2, '--': False})

        doc = '''usage: prog -v...'''
        sys.argv = ['prog']
        self.fail(doc)
        sys.argv = ['prog', '-v']
        self.eq(doc, {'-v': 1, '--': False})

        sys.argv = ['prog', '-vv']
        self.eq(doc, {'-v': 2, '--': False})

        sys.argv = ['prog', '-vvvvvv']
        self.eq(doc, {'-v': 6, '--': False})

        # Note: different from docopt
        doc = '''usage: prog [-vvv | -vv | -v]'''
        sys.argv = ['prog']
        self.eq(doc, {'-v': 0, '--': False})
        sys.argv = ['prog', '-v']
        self.eq(doc, {'-v': 1, '--': False})
        sys.argv = ['prog', '-vv']
        self.eq(doc, {'-v': 2, '--': False})
        sys.argv = ['prog', '-vvvv']
        self.fail(doc)

    def test_count_command(self):
        doc = '''usage: prog [go]'''
        sys.argv = ['prog', 'go']
        self.eq(doc, {'go': True, '--': False})

        doc = '''usage: prog [go go]'''
        sys.argv = ['prog']
        self.eq(doc, {'go': 0, '--': False})
        sys.argv = ['prog', 'go', 'go']
        self.eq(doc, {'go': 2, '--': False})
        sys.argv = ['prog', 'go', 'go', 'go']
        self.fail(doc)

        doc = '''usage: prog go...'''
        sys.argv = ['prog', 'go', 'go', 'go', 'go', 'go']
        self.eq(doc, {'go': 5, '--': False})

    def test_option_not_include(self):
        doc = '''usage: prog [options] [-a]

options: -a
         -b'''
        sys.argv = ['prog', '-a']
        self.eq(doc, {'-a': True, '-b': False, '--': False})
        sys.argv = ['prog', '-aa']
        self.fail(doc)

    def test_option_shortcut(self):
        doc = '''Usage: prog [options] A

Options:
    -q  Be quiet
    -v  Be verbose.'''
        sys.argv = ['prog', 'arg']
        self.eq(doc, {'A': 'arg', '-q': False, '-v': False,
                      '--': False})

        sys.argv = ['prog', '-v', 'arg']
        self.eq(doc, {'A': 'arg', '-q': False, '-v': True,
                      '--': False})

        sys.argv = ['prog', '-q', 'arg']
        self.eq(doc, {'A': 'arg', '-q': True, '-v': False,
                      '--': False})

    def test_value_always_list(self):
        doc = '''usage: prog [NAME [NAME ...]]'''

        sys.argv = ['prog', 'a', 'b']
        self.eq(doc, {'NAME': ['a', 'b'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'NAME': [], '--': False})

    def test_ommit_default_opt_value(self):
        doc = '''usage: prog [options]

options:
 -a               Add
 -m <msg>         Message
 -c <value>...    Test
'''

        sys.argv = ['prog']
        self.eq(doc, {'-a': False, '-m': None, '-c': [],
                      '--': False})

        sys.argv = ['prog', '-a']
        self.eq(doc, {'-a': True, '-m': None, '-c': [],
                      '--': False})

    def test_fake_git(self):
        doc = '''usage: git [-v | --verbose]'''
        sys.argv = ['git', '-v']
        self.eq(doc, {'-v': True, '--verbose': False,
                      '--': False})

        doc = '''usage: git remote [-v | --verbose]'''
        sys.argv = ['git', 'remote', '-v']
        self.eq(doc, {'-v': True, '--verbose': False, 'remote': True,
                      '--': False})

    def test_empty_usage(self):
        doc = '''usage: prog'''
        sys.argv = ['prog']
        self.eq(doc, {'--': False})

        doc = '''
        usage: prog
               prog <a> <b>'''
        sys.argv = ['prog', '1', '2']
        self.eq(doc, {'<a>': '1', '<b>': '2', '--': False})
        sys.argv = ['prog']
        self.eq(doc, {'<a>': None, '<b>': None, '--': False})

        doc = '''
        usage: prog <a> <b>
               prog'''
        sys.argv = ['prog', '1', '2']
        self.eq(doc, {'<a>': '1', '<b>': '2', '--': False})
        sys.argv = ['prog']
        self.eq(doc, {'<a>': None, '<b>': None, '--': False})

    # This does not support so far
    # r"""usage: prog [--file=<f>]"""
    # $ prog
    # {"--file": null}

    def test_dif_arg_of_opt(self):
        doc = '''usage: prog [--file=<f>]

options: --file <a>
'''
        sys.argv = ['prog']
        self.eq(doc, {'--file': None, '--': False})

    def test_unusual_arg_name(self):
        doc = '''Usage: prog [-a <host:port>]

Options: -a, --address <host:port>  TCP address[default: localhost:6283]
'''
        sys.argv = ['prog']
        self.eq(doc, {'--address': 'localhost:6283', '-a': 'localhost:6283',
                      '--': False})

    def test_usage_without_option_section_matching_options(self):
        # This now support even without "Option" section
        doc = '''usage: prog --long=<arg> ...'''
        # but it is euqal to:
        doc2 = '''usage: prog --long=(<arg> ...)'''

        sys.argv = ['prog', '--long', 'one']
        self.eq(doc, {'--long': ['one'], '--': False})
        self.eq(doc2, {'--long': ['one'], '--': False})

        sys.argv = ['prog', '--long', 'one', 'two', 'three']
        self.eq(doc, {'--long': ['one', 'two', 'three'], '--': False})
        self.eq(doc2, {'--long': ['one', 'two', 'three'], '--': False})

        doc = '''usage: prog (--long=<arg>) ...'''
        sys.argv = ['prog', '--long', 'one']
        self.eq(doc, {'--long': ['one'], '--': False})

        sys.argv = ['prog', '--long', 'one', '--long=two', '--long=three']
        self.eq(doc, {'--long': ['one', 'two', 'three'], '--': False})

    def test_multiple_ele_repeat(self):
        doc = '''usage: prog (go <direction> --speed=<km/h>)...

Options:
  --speed=<km/h>'''
        sys.argv = ['prog',  'go', 'left',
                    '--speed=5',  'go', 'right', '--speed=9']
        self.eq(doc,
                {"go": 2, "<direction>": ["left", "right"],
                 "--speed": ["5", "9"], '--': False})

    def test_option_sct_with_option(self):
        doc = '''usage: prog [options] -a

options: -a
'''
        sys.argv = ['prog', '-a']
        self.eq(doc, {'-a': True, '--': False})

    def test_option_default_split(self):
        doc = '''usage: prog [-o <o>]...

options: -o <o>  [default: x]
'''
        sys.argv = ['prog', '-o', 'this', '-o', 'that']
        self.eq(doc, {'-o': ['this', 'that'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'-o': ['x'], '--': False})

    def test_option_default_split_with_repeat(self):
        doc = '''usage: prog [-o <o>]...

options: -o <o>  [default: x y]
'''

        sys.argv = ['prog', '-o', 'this']
        self.eq(doc, {'-o': ['this'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'-o': ['x', 'y'], '--': False})

        doc = '''usage: prog [-o [<o>]...]

options: -o [<o>]...  [default: x y]
'''

        sys.argv = ['prog', '-o', 'this']
        self.eq(doc, {'-o': ['this'], '--': False})

        sys.argv = ['prog']
        self.eq(doc, {'-o': ['x', 'y'], '--': False})

    # Different from docopt
    def test_docopt_issue_56(self):
        doc = '''Usage: foo (--xx=<x>|--yy=<y>)...

Options:
  --xx=<x>
  --yy=<y>'''
        sys.argv = ['prog', '--xx=1', '--xx=2']
        self.eq(doc, {'--xx': ['1', '2'], '--yy': [], '--': False})

        sys.argv = ['prog', '--xx=1', '--yy=2']
        self.fail(doc)

    def test_posixly_correct_tokenization(self):
        doc = '''usage: prog [<input file>]'''

        sys.argv = ['prog', 'f.txt']
        self.eq(doc, {'<input file>': 'f.txt', '--': False})

        # Note: different from docopt: need `options:`
        doc = '''usage: prog [--input=<file name>]...

        Options:
          --input=<file name>'''

        sys.argv = ['prog', '--input', 'a.txt', '--input=b.txt']
        self.eq(doc, {'--input': ['a.txt', 'b.txt'], '--': False})

        doc = '''usage: prog [--input=<file name>]...

        Options:
          --input=<file name>'''

        sys.argv = ['prog', '--input', 'a.txt', '--input=b.txt']
        self.eq(doc, {'--input': ['a.txt', 'b.txt'], '--': False})

    def test_docopt_issue_85_with_subcommands(self):
        doc = '''
        usage: prog good [options]
               prog fail [options]

        options: --loglevel=N'''

        sys.argv = ['prog', 'fail', '--loglevel', '5']
        self.eq(doc, {'good': False, 'fail': True, '--loglevel': '5',
                      '--': False})

    def test_usage_section_syntax(self):
        doc = '''usage:prog --foo'''

        sys.argv = ['prog', '--foo']
        self.eq(doc, {'--foo': True, '--': False})

        # Not support in docpie
        #
        # r"""PROGRAM USAGE: prog --foo"""
        # $ prog --foo
        # {"--foo": true}
        #
        # r"""Usage: prog --foo
        #            prog --bar
        # NOT PART OF SECTION"""
        # $ prog --foo
        # {"--foo": true, "--bar": false}
        #
        # r"""Usage:
        #  prog --foo
        #  prog --bar
        # NOT PART OF SECTION"""
        # $ prog --foo
        # {"--foo": true, "--bar": false}

        doc = '''Usage:
 prog --foo
 prog --bar

NOT PART OF SECTION'''

        sys.argv = ['prog', '--foo']
        self.eq(doc, {'--foo': True, '--bar': False, '--': False})

    def test_option_section_syntax(self):
        doc = """Usage: prog [options]

        global options: --foo
        local options: --baz
                       --bar
        other options:
         --egg
         --spam

        -not-an-option-  # different from docopt here

        """

        sys.argv = ['prog', '--baz', '--egg']
        expect = {"--foo": False, "--baz": True, "--bar": False,
                  "--egg": True, "--spam": False, "--": False}
        self.eq(doc, expect)

    def test_usage_section_of_docpie(self):
        doc = '''
Usage: prog <a>
       prog <b>'''

        sys.argv = ['prog', 'go!']
        self.eq(doc, {'<a>': 'go!', '<b>': None, '--': False})

        doc = '''
Usage:
  prog a b
  prog c d'''

        sys.argv = ['prog', 'c', 'd']
        self.eq(doc, {'a': False, 'b': False, 'c': True, 'd': True,
                      '--': False})

        doc = '''
Usage:
    prog a b
      c d
    prog a b
         e f'''

        sys.argv = ['prog', 'a', 'b', 'e', 'f']
        self.eq(doc, {'a': True, 'b': True, 'c': False, 'd': False, 'e': True,
                      'f': True, '--': False})

    def test_option_secion_of_docpie(self):
        doc = '''Usage: prog [options]

Options:
-a  a description
-b
  also description
-c
'''
        sys.argv = ['prog']
        self.eq(doc, {'-a': False, '-b': False, '-c': False,
                      '--': False})

        doc = '''
Usage: prog [options]

Options: -a, --all=<here>
             --you can write discription like this even starting
             with `--`, as long as you ensure it indent more
             (at least 2 more space) spaces.
         -b, --brillant=<there>  You can alse write  a long long long long
                                 long long long long description at the same
                                 line. But all the following line should have
                                 the same indent.
         -c, --clever=<where>
            docopt have more strict `default` syntax. It must startswith
            `[default: `(note the space after colon), following your default
            value, and endswith `]`. The following default will be an empty
            string.[default: ]
         -d, --default=<strict>
            And this default will be a space. [default:  ]
         -e, --escape=[<space>]  Though it's not standrad POSIX, docpie support
                                 flag that expecting uncertain numbers of args
                                 but it will gives you a waring.
                                 You can disabled the waring by
                                 ```
                                 import logging
                                 logging.getLogger().setLevel(logging.CRITICEL)
                                 ```
                                 the logger name of docpie is `docpie`
                                 BTW, this default will not work because it
                                 endswith a dot, and the defualt value (because
                                 of `[<space>]`) will be `None` instead of
                                 `False`[default: not-work].
         -t, --thanks=<my-friend>...
            when an option accept multiple values, the default will be
            seperated by white space(space, tab, ect.)[default: Calvary Brey]
        '''
        sys.argv = ['prog', '--all=all', '-b', 'brillant']
        self.eq(doc, {'-a': 'all', '--all': 'all',
                      '-b': 'brillant', '--brillant': 'brillant',
                      '-c': '', '--clever': '',
                      '-d': ' ', '--default': ' ',
                      '-e': None, '--escape': None,
                      '-t': ['Calvary', 'Brey'],
                      '--thanks': ['Calvary', 'Brey'],
                      '--': False})

    def test_option_abnormal_usage(self):
        doc = '''
        Usage: prog [options]

        Options:
        -a..., --all ...               -a is countable
        -b<sth>..., --boring=<sth>...  inf argument
        -c <a> [<b>]                   optional & required args
        -d [<arg>]                     optional arg
        '''

        result = docpie(doc, 'prog -aa -a -b go go go -c sth else')
        self.assertEqual(result, {'-a': 3, '--all': 3,
                                  '-b': ['go', 'go', 'go'],
                                  '--boring': ['go', 'go', 'go'],
                                  '-c': ['sth', 'else'],
                                  '-d': None,
                                  '--': False})
        doc = '''
        Usage:
         test.py [options]

        Options:
         -a ...    Some help.
         -b ...    Some help.[default: a b]
         -c
        '''
        result = docpie(doc, 'prog -bb -b'.split())
        self.assertEqual(result, {'-a': 0, '-b': 3, '-c': False, '--': False})

    def test_option_dif_write(self):
        doc = '''
        Usage: program.py --path=<path>...

        Options: --path=<path>...     the path you need'''

        sys.argv = ['program.py', '--path', './here', './there']
        self.eq(doc, {'--path': ['./here', './there'], '--': False})

        doc = '''
        Usage: program.py (--path=<path>)...

        Options: --path=<path>     the path you need'''

        sys.argv = ['program.py', '--path=./here', '--path', './there']
        self.eq(doc, {'--path': ['./here', './there'], '--': False})

    def test_name(self):
        doc = '''Usage:
        python docpie.py a
        $ python docpie.py b
        $ sudo python docpie.py c'''

        sys.argv = ['prog', 'a']
        self.assertEqual(docpie(doc, name='docpie.py'),
                         {'a': True, 'b': False, 'c': False,
                          '--': False})

        sys.argv = ['prog', 'b']
        self.assertEqual(docpie(doc, name='docpie.py'),
                         {'a': False, 'b': True, 'c': False,
                          '--': False})

        sys.argv = ['prog', 'c']
        self.assertEqual(docpie(doc, name='docpie.py'),
                         {'a': False, 'b': False, 'c': True,
                          '--': False})

    def test_easy_balance_required(self):
        doc = '''Usage: prog <a>... <b> <c>'''

        sys.argv = ['prog', '1', '2', '3', '4']
        self.eq(doc, {'<a>': ['1', '2'], '<b>': '3', '<c>': '4', '--': False})

        sys.argv = ['prog', '1', '2', '3']
        self.eq(doc, {'<a>': ['1'], '<b>': '2', '<c>': '3', '--': False})

        sys.argv = ['prog', '1', '2']
        self.fail(doc)

    def test_easy_balance_optional(self):
        doc = '''Usage: prog [<a>]... <b> <c>'''

        sys.argv = ['prog', '1', '2', '3', '4']
        self.eq(doc, {'<a>': ['1', '2'], '<b>': '3', '<c>': '4', '--': False})

        sys.argv = ['prog', '1', '2', '3']
        self.eq(doc, {'<a>': ['1'], '<b>': '2', '<c>': '3', '--': False})

        # change in 0.2.6
        # When borrowing value, the lender will at least keep one value
        # for itself
        sys.argv = ['prog', '1', '2']
        # self.eq(doc, {'<a>': [], '<b>': '1', '<c>': '2', '--': False})
        self.fail(doc)

        sys.argv = ['prog', '1']
        self.fail(doc)

    def test_option_order(self):
        doc = '''
        Usage:
            prog [options] -a <a> -b <b> -c <c>

        Options:
            -a <a>
            -b <b>
            -c <c>'''

        sys.argv = 'prog -c c -b b -a a'.split()
        self.eq(doc, {'-a': 'a', '-b': 'b', '-c': 'c', '--': False})
        sys.argv = 'prog -c c -aa -bb'.split()
        self.eq(doc, {'-a': 'a', '-b': 'b', '-c': 'c', '--': False})
        sys.argv = 'prog -bb -aa -cc'.split()
        self.eq(doc, {'-a': 'a', '-b': 'b', '-c': 'c', '--': False})

    def test_order(self):
        doc = '''
        Usage:
            prog -a cmd1 -b cmd2 -c cmd3
        '''

        sys.argv = 'prog -a cmd1 -b cmd2 -c cmd3'.split()
        self.eq(doc, {'-a': True, '-b': True, '-c': True,
                      'cmd1': True, 'cmd2': True, 'cmd3': True,
                      '--': False})

        sys.argv = 'prog -c cmd1 -b cmd2 -a cmd3'.split()
        self.eq(doc, {'-a': True, '-b': True, '-c': True,
                      'cmd1': True, 'cmd2': True, 'cmd3': True,
                      '--': False})

        sys.argv = 'prog -c cmd1 cmd2 -a -b cmd3'.split()
        self.eq(doc, {'-a': True, '-b': True, '-c': True,
                      'cmd1': True, 'cmd2': True, 'cmd3': True,
                      '--': False})

        sys.argv = 'prog -a cmd2 cmd1 -b -c cmd3'.split()
        self.fail(doc)

        sys.argv = 'prog -a -b -c cmd3 cmd2 cmd1'.split()
        self.fail(doc)

    def test_balace_value_bug(self):
        doc = '''
        Usage:
            prog a b <c>...
        '''

        sys.argv = 'prog c c c'.split()
        self.fail(doc)

    def test_double_dashes_when_has_element(self):
        doc = '''
        Usage:
            prog [cmd] [--option] [<arg>]...'''

        sys.argv = 'prog cmd --option arg -- -- - arg -arg --arg'.split()
        self.eq(doc, {'--': True,
                      '--option': True,
                      '<arg>': ['arg', '--', '-', 'arg', '-arg', '--arg'],
                      'cmd': True})

        sys.argv = 'prog cmd arg -- - -- -arg --arg'.split()
        self.eq(doc, {'--': True,
                      '--option': False,
                      '<arg>': ['arg', '-', '--', '-arg', '--arg'],
                      'cmd': True})

        doc = '''Usage: pie.py [-v] [<file>...]'''
        sys.argv = 'pie.py -- -v --help'.split()
        self.eq(doc, {'-v': False, '<file>': ['-v', '--help'], '--': True})

    def test_new_bracket_meaning(self):
        doc = '''Usage: prog [cmd --opt <arg>]'''

        sys.argv = 'prog arg --opt cmd'.split()
        self.fail(doc)

        sys.argv = 'prog arg cmd --opt'.split()
        self.fail(doc)

        sys.argv = 'prog --opt arg cmd'.split()
        self.fail(doc)

        sys.argv = 'prog --opt cmd arg'.split()
        self.eq(doc, {'--opt': True, '<arg>': 'arg', 'cmd': True, '--': False})

        sys.argv = 'prog cmd --opt arg'.split()
        self.eq(doc, {'--opt': True, '<arg>': 'arg', 'cmd': True, '--': False})

        sys.argv = 'prog cmd arg --opt'.split()
        self.eq(doc, {'--opt': True, '<arg>': 'arg', 'cmd': True, '--': False})

    def test_new_bracket_meaning_in_opt(self):
        doc = 'Usage: prog [-dir]'
        pa_doc = 'Usage: prog (-dir)'
        sys.argv = 'prog -rid'.split()
        self.eq(doc, {'-r': True, '-i': True, '-d': True, '--': False})
        self.eq(pa_doc, {'-r': True, '-i': True, '-d': True, '--': False})

        sys.argv = 'prog -id'.split()
        self.eq(doc, {'-r': False, '-i': True, '-d': True, '--': False})
        self.fail(pa_doc)

        sys.argv = 'prog -i'.split()
        self.eq(doc, {'-r': False, '-i': True, '-d': False, '--': False})
        self.fail(pa_doc)

        sys.argv = 'prog'.split()
        self.eq(doc, {'-r': False, '-i': False, '-d': False, '--': False})
        self.fail(pa_doc)

    def test_arg_shadow_cmd(self):
        doc = 'Usage: prog cmd --flag <arg>'
        # <arg> should not take `cmd`
        sys.argv = 'prog cmd --flag sth'.split()
        self.eq(doc, {'cmd': True, '--flag': True, '<arg>': 'sth',
                      '--': False})
        doc = 'Usage: prog [cmd --flag <arg>]'
        self.eq(doc, {'cmd': True, '--flag': True, '<arg>': 'sth',
                      '--': False})

    def test_either_in_repeat(self):
        doc = '''Usage: prog (a [this | that])...'''

        sys.argv = 'prog a'.split()
        self.eq(doc, {'--': False, 'a': 1, 'that': 0, 'this': 0})

        sys.argv = 'prog a this a this a this a'.split()
        self.eq(doc, {'--': False, 'a': 4, 'that': 0, 'this': 3})

        sys.argv = 'prog a this a this a that a'.split()
        self.fail(doc)

    def test_option_unit_stack(self):
        doc = '''Usage: pie.py [command] [--option] [<argument>]'''

        sys.argv = 'prog --option command arg'.split()
        self.eq(doc, {'--option': True, 'command': True, '<argument>': 'arg',
                      '--': False})

        sys.argv = 'prog --option command -- arg'.split()
        self.eq(doc, {'--option': True, 'command': True, '<argument>': 'arg',
                      '--': True})

        sys.argv = 'prog --option -- command arg'.split()
        self.eq(doc, {'--option': True, 'command': True, '<argument>': 'arg',
                      '--': True})

    def test_long_option_short(self):
        doc = '''Usage: prog [options]

        Options:
            --prefix
            --prefer
            --prepare
        '''

        sys.argv = 'prog --prefi'.split()
        self.eq(doc, {'--prefix': True, '--prefer': False, '--prepare': False,
                      '--': False})

        sys.argv = 'prog --prefe'.split()
        self.eq(doc, {'--prefix': False, '--prefer': True, '--prepare': False,
                      '--': False})

        sys.argv = 'prog --prep'.split()
        self.eq(doc, {'--prefix': False, '--prefer': False, '--prepare': True,
                      '--': False})

    def test_auto_expand(self):
        doc = 'Usage: prog [--prefix --prefer --prepare] [<args>...]'

        sys.argv = 'prog -- --prefi --prefe --prep'.split()
        self.eq(doc, {'--prefix': False, '--prefer': False, '--prepare': False,
                      '--': True, '<args>': ['--prefi', '--prefe', '--prep']})

        doc = 'Usage: prog [--prefix --prefer --prepare] [<args>...]'

        sys.argv = \
            'prog --prepare --prefer --prefix -- --prefi --prefe --prep'.split()
        self.eq(doc, {'--prefix': True, '--prefer': True, '--prepare': True,
                      '--': True, '<args>': ['--prefi', '--prefe', '--prep']})

    def test_auto_expand_raise(self):
        if hasattr(self, 'assertRaisesRegex'):
            doc = 'Usage: prog [--prefix --prefer --prepare] [<args>...]'

            sys.argv = 'prog --pre'.split()
            with self.assertRaisesRegex(
                    DocpieExit, "^--pre is not a unique prefix:"):
                docpie(doc)

            sys.argv = 'prog --not-here'.split()
            with self.assertRaisesRegex(
                    DocpieExit, "^Unknown option: --not-here"):
                docpie(doc)

    def test_new_either(self):
        doc = '''Usage: prog [-v | -vv | -vvv] [<arg>]'''

        sys.argv = ['prog']
        self.eq(doc, {'-v': 0, '<arg>': None, '--': False})

        sys.argv = ['prog', '-v']
        self.eq(doc, {'-v': 1, '<arg>': None, '--': False})

        sys.argv = ['prog', '-vv']
        self.eq(doc, {'-v': 2, '<arg>': None, '--': False})

        sys.argv = ['prog', '-vvv']
        self.eq(doc, {'-v': 3, '<arg>': None, '--': False})

        sys.argv = ['prog', '-vvvv']
        self.fail(doc)

        sys.argv = ['prog', '-vv', '--', '-v']
        self.eq(doc, {'-v': 2, '<arg>':'-v' ,'--': True})

        doc = '''Usage: prog (<a> | <b> <c>) <d>'''
        doc2 = '''Usage: prog (<b> <c> | <a>) <d>'''

        sys.argv = ['prog', 'a', 'd']
        self.eq(doc, {'<a>': 'a', '<b>': None, '<c>': None, '<d>': 'd',
                      '--': False})
        self.eq(doc2, {'<a>': 'a', '<b>': None, '<c>': None, '<d>': 'd',
                       '--': False})

        sys.argv = ['prog', 'b', 'c', 'd']
        self.eq(doc, {'<a>': None, '<b>': 'b', '<c>': 'c', '<d>': 'd',
                      '--': False})
        self.eq(doc2, {'<a>': None, '<b>': 'b', '<c>': 'c', '<d>': 'd',
                       '--': False})

    def test_issue_1(self):
        doc = '''Usage: prog [cmd1 cmd2]'''
        sys.argv = ['prog', 'cmd2', 'cmd1']
        self.fail(doc)

        sys.argv = ['prog', 'cmd1', 'cmd2']
        self.eq(doc, {'cmd1': True, 'cmd2': True, '--': False})

        sys.argv = ['prog', 'cmd1', '--', 'cmd2']
        self.eq(doc, {'cmd1': True, 'cmd2': True, '--': True})

    def test_jsonlize(self):
        doc = """
        Usage:
            serialization dump [options] [--path=<path>]
            serialization load [options] [preview] [--path=<path>]
            serialization clear
            serialization preview

        Options:
            -p, --path=<path>           save or load path or filename[default: ./]
            -f, --format=<format>...    save format, "json" or "pickle"
                                        [default: json pickle]
            -n, --name=<name>           save or dump filename without extension,
                                        default is the same as this file
            -h, -?                      print usage
            --help                      print this message
            -v, --version               print the version
        """

        pie = Docpie(doc, version="Alpha")
        dic = pie.convert_to_dict()
        s = json.dumps(dic)
        d = json.loads(s)
        new_pie = pie.convert_to_docpie(d)

        self.assertEqual(pie.usages, new_pie.usages)
        self.assertEqual(pie.options, new_pie.options)
        self.assertEqual(pie.version, new_pie.version)

    def test_repeat_in_usage(self):
        doc = '''
        Usage: prog [options]
                    [--repeat=<sth> --repeat=<sth>]
                    [--another-repeat=<sth> --another-repeat=<sth>]
                    [cmd cmd]
                    [<arg> <arg>]

        Options:
            --repeat=<arg>          the repeatable flag [default: here there]
            --another-repeat=<sth>  the repeatable flag
        '''

        sys.argv = ['prog']
        self.eq(doc, {'--repeat': ['here', 'there'], '--another-repeat': [],
                      'cmd': 0, '<arg>': [],
                      '--': False})

        sys.argv = ['prog', '--repeat=1', '--repeat=2',
                    '--another-repeat=1', '--another-repeat=2']
        self.eq(doc, {'--repeat': ['1', '2'], '--another-repeat': ['1', '2'],
                      'cmd': 0, '<arg>': [],
                      '--': False})

        sys.argv = ['prog', '--repeat=1', '--repeat=2', '--repeat=3'
                                                        '--another-repeat=1', '--another-repeat=2']
        self.fail(doc)

        sys.argv = ['prog', '--repeat=1', '--repeat=2',
                    '--another-repeat=1', '--another-repeat=2',
                    '--another-repeat=3']
        self.fail(doc)

    def test_stack_value_in_usage_with_upper(self):
        # Don't do this!
        doc = '''
        Usage: prog -oFILE

        Options: -o FILE    output file'''

        sys.argv = ['prog', '-o', '/dev/null']
        self.eq(doc, {'-o': '/dev/null', '--': False})

    def test_auto_expand_raise_short_option(self):
        if hasattr(self, 'assertRaisesRegex'):
            doc = 'Usage: prog -abc'

            sys.argv = 'prog -d'.split()
            with self.assertRaisesRegex(DocpieExit, "^Unknown option: "):
                docpie(doc)

            with StdoutRedirect() as f:
                doc = 'Usage: prog -abc'

                sys.argv = 'prog -ha'.split()
                # help
                with self.assertRaises(SystemExit) as e:
                    docpie(doc)

                args = e.exception.args
                if len(args) == 1:
                    self.assertIsNone(args[0])  # pypy
                else:
                    self.assertEqual(e.exception.args, ())

            self.assertEqual(f.read(), 'Usage: prog -abc\n')

    def test_auto_expand_raise_short_option_stack(self):
        if hasattr(self, 'assertRaisesRegex'):
            doc = 'Usage: prog -abc'

            sys.argv = 'prog -ad'.split()
            with self.assertRaisesRegex(DocpieExit, "^Unknown option: "):
                docpie(doc)

            doc = 'Usage: prog [-abc]'
            sys.argv = 'prog -ah'.split()

            with StdoutRedirect() as f:
                # help
                with self.assertRaises(SystemExit) as e:
                    docpie(doc, helpstyle='raw')

            args = e.exception.args
            if len(args) == 1:
                self.assertIsNone(args[0])
            else:
                self.assertEqual(args, ())

            self.assertEqual(f.read(), 'Usage: prog [-abc]')

    def test_option_disorder_match(self):
        doc = 'Usage: prog -b -a'
        sys.argv = 'prog -ab'.split()
        self.eq(doc, {'-a': True, '-b': True, '--': False})

    def test_option_stack_in_usage(self):
        doc = 'Usage: prog -b<sth> -a'
        sys.argv = 'prog -abb'.split()
        self.eq(doc, {'-a': True, '-b': 'b', '--': False})

    def test_auto_handler(self):
        doc = 'Usage: prog -a<sth>'

        sys.argv = 'prog -ah'.split()
        self.eq(doc, {'-a': 'h', '--': False})

        if hasattr(self, 'assertRaises'):
            if sys.version_info[:2] == (2, 6):
                sys.stdout.write('skip test_auto_handler')
                sys.stdout.flush()
                return
            with StdoutRedirect() as f:
                sys.argv = ['prog', '-ha']
                with self.assertRaises(SystemExit) as e:
                    docpie(doc)
                    if e is not None:
                        self.assertEqual(str(e), '')
                    self.assertEqual(f.read(), 'Usage: prog -a<sth>')

                sys.argv = ['prog', '-xxxh']
                with self.assertRaises(SystemExit) as e:
                    docpie(doc)
                    if e is not None:
                        self.assertEqual(str(e), '')
                    self.assertEqual(f.read(), 'Usage: prog -a<sth>')

                sys.argv = ['prog', '-xvx']
                with self.assertRaises(SystemExit) as e:
                    docpie(doc, version='0.0.0')
                    if e is not None:
                        self.assertEqual(str(e), '')
                    self.assertEqual(f.read(), '0.0.0')

    def test_multi_options_section(self):
        doc = '''
        Usage: prog [options]

        Options:
            -a
            -b

        Advanced Options: -c
                          -d'''

        sys.argv = 'prog -a -c'.split()
        self.eq(doc, {'-a': True, '-b': False, '-c': True, '-d': False,
                      '--': False})

    def test_inside_angle_brancket(self):
        # "<+|-|*|/>" should not be interpreted as "<+ | - | * | />"
        doc = '''Usage:
        prog <value> (<+|-|*|/> <value>)...'''

        sys.argv = 'prog 1 + 2 - 3 * 4 / 5'.split()
        self.eq(doc, {'<+|-|*|/>': ['+', '-', '*', '/'],
                      '<value>': ['1', '2', '3', '4', '5'],
                      '--': False})

    def test_fix_init_bug(self):
        doc = '''

Usage:
  prog -v | --version

Options:
  -v, --version     Show version.
        '''

        if (sys.version_info[0] == 2 and sys.version_info[1] <= 6 or
                not hasattr(self, 'assertRaises')):
            sys.stdout.write('skip test_fix_init_bug')
            sys.stdout.flush()
            return

        sys.argv = 'prog sth -v'.split()
        with StdoutRedirect() as f:
            with self.assertRaises(SystemExit) as e:
                docpie(doc, version='1.1.1')
        info = f.read()
        try:
            unicode
        except NameError:
            pass
        else:
            if isinstance(info, unicode):
                info = str(info)
        self.assertEqual(info, '1.1.1\n')
        args = e.exception.args
        if len(args) == 1:
            if (platform.python_implementation().lower() == 'pypy' and
                        sys.version_info == (2, 7, 3, 'final', 42)):
                # it will give args == (0,), why?
                return

            self.assertIsNone(args[0])
        else:
            self.assertEqual(args, ())

    def test_stack_value_with_short_option(self):
        doc = "Usage: prog -a<val>"
        sys.argv = ['prog', '-ah']
        self.eq(doc, {'-a': 'h', '--': False})

        doc = """Usage: prog -a <sth>

        Options:
            -a <sth>"""

        sys.argv = ['prog', '-ah']
        self.eq(doc, {'-a': 'h', '--': False})

        doc = """Usage: prog -a<sth>

        Options:
            -a <sth>"""

        sys.argv = ['prog', '-ah']
        self.eq(doc, {'-a': 'h', '--': False})

        doc = "Usage: prog -aVAL"
        sys.argv = ['prog', '-aval']
        self.fail(doc)

        doc = """Usage: prog -a VAL

        Options:
            -a <sth>"""

        sys.argv = ['prog', '-ah']
        self.eq(doc, {'-a': 'h', '--': False})

        doc = """Usage: prog -aVAL

        Options:
            -a <sth>"""

        sys.argv = ['prog', '-ah']
        self.eq(doc, {'-a': 'h', '--': False})

    def test_windows_style_break_line(self):
        doc = (
            '\r\n'
            'Usage:\r\n'
            '   prog [options] cmd1\r\n'
            '   prog [options] cmd2\r\n'
            '\r\n'
            'Options:\r\n'
            '   -o --option    an option\r\n'
            '\r\n'
            'Another Options:\r\n'
            '   -a              another option\r\n'
            'Near Options:\r\n'
            '   -n              a closer option secion'
        )

        sys.argv = ['prog', 'cmd2']
        expect = {'cmd1': False, 'cmd2': True, '-o': False,
                  '--option': False, '-a': False, '-n': False,
                  '--': False}
        self.eq(doc.replace('\r', ''), expect)
        self.eq(doc, expect)

    def test_usage_content_options_title(self):
        doc = """
        Usage: prog <Options:>

        Options:
            -h, --help"""

        sys.argv = ['prog', 'sth']
        expect = {'<Options:>': 'sth', '-h': False, '--help': False,
                  '--': False}
        self.eq(doc, expect)

    def test_repeat_follow_command(self):
        doc = """
        Usage: prog <a>... <b> cmd"""

        sys.argv = ['prog', '1', '2', '3', 'cmd']
        expect = {'<a>': ['1', '2'], '<b>': '3', 'cmd': True, '--': False}
        self.eq(doc, expect)

        doc = """Usage: prog <a>... cmd <b>"""

        sys.argv = ['prog', '1', '2', 'cmd', '3']
        expect = {'<a>': ['1', '2'], 'cmd': True, '<b>': '3', '--': False}
        self.eq(doc, expect)

    def test_repeat_required_grouped(self):
        doc = """Usage: prog (<a> <b>)... <c> <d>"""
        sys.argv = ['prog', 'a', 'b', 'a', 'b', 'c', 'd']
        expect = {'<a>': ['a', 'a'], '<b>': ['b', 'b'], '<c>': 'c', '<d>': 'd',
                  '--': False}
        self.eq(doc, expect)

        sys.argv = ['prog', 'a', 'b', 'a', 'b', 'c']
        self.fail(doc)

        sys.argv = ['prog', 'a', 'b', 'c', 'd']
        expect = {'<a>': ['a'], '<b>': ['b'], '<c>': 'c', '<d>': 'd',
                  '--': False}
        self.eq(doc, expect)

        sys.argv = ['prog', 'a', 'b']
        self.fail(doc)

    def test_repeat_optional_grouped(self):
        doc = """Usage: prog [<a> <b>]... <c> <d>"""
        sys.argv = ['prog', 'a', 'b', 'a', 'b', 'c', 'd']
        expect = {'<a>': ['a', 'a'], '<b>': ['b', 'b'], '<c>': 'c', '<d>': 'd',
                  '--': False}
        self.eq(doc, expect)

        sys.argv = ['prog', 'a', 'b', 'a', 'c', 'd']
        expect = {'<a>': ['a', 'a'], '<b>': ['b'], '<c>': 'c', '<d>': 'd',
                  '--': False}
        self.eq(doc, expect)

        sys.argv = ['prog', 'a', 'b', 'c', 'd']
        expect = {'<a>': ['a'], '<b>': ['b'], '<c>': 'c', '<d>': 'd',
                  '--': False}
        self.eq(doc, expect)

        sys.argv = ['prog', 'c', 'd']
        self.fail(doc)
        # expect = {'<a>': [], '<b>': [], '<c>': 'c', '<d>': 'd', '--': False}
        # self.eq(doc, expect)

    def test_issue_3(self):
        doc = """
        Usage: prog [options] --keep
               prog [options]

        Options:
            -k, --keep"""

        # --keep followed by an option which is not in `Options`
        # this will RANDOMLY FAIL!!!!
        sys.argv = ['prog', '--keep']
        expect = {'--keep': True, '-k': True,
                  '--': False}
        # usually 1 fail out of 3
        for _ in range(6):
            self.eq(doc, expect)

    def test_issue_3_not_alias_for_opt(self):
        expect = {'-k': True, '--keep': True, '--': False}

        doc1 = """
        Usage: prog -k

        Options:
            -k, --keep"""

        doc2 = """
        Usage: prog --keep

        Options:
            -k, --keep"""

        argv1 = ['prog', '-k']
        argv2 = ['prog', '--keep']

        for doc in (doc1, doc2):
            for argv in (argv1, argv2):
                sys.argv = argv
                self.eq(doc, expect)

    def test_new_fix_for_options_not_raise(self):
        doc = """
        Usage:
            prog [options]

        Options:
        """
        sys.argv = ['prog']
        self.eq(doc, {'--': False})

        sys.argv = ['prog', 'sth']
        self.fail(doc)

    def test_option_not_reset_cause_fail(self):
        doc = """
        Usage: prog [options] a
               prog [options] b

        Options:
            -a"""

        sys.argv = ['prog', '-a', 'b']
        self.eq(doc, {'-a': True, 'a': False, 'b': True, '--': False})

    def test_unstd_option_value_cause_double_dashes_failed(self):
        doc = """
        Usage: prog [options] <arg>

        Options:
            --force[=<value>]
            -a
        """

        sys.argv = ['prog', '--force', '--', 'val']
        expect = {'--force': None, '--': True, '<arg>': 'val', '-a': False}
        self.eq(doc, expect)

        sys.argv = ['prog', '--force', '-a', 'val']
        expect = {'--force': None, '--': False, '<arg>': 'val', '-a': True}
        self.eq(doc, expect)

    def test_option_value_handle_dashes(self):
        # not standard
        doc = """Usage: prog [options] C

        Options:
            --all=[A B]
        """

        sys.argv = ['prog', '--all', '--', 'A', 'B', 'C']
        self.fail(doc)

        sys.argv = ['prog', '--all', 'A', '--', 'B', 'C']
        self.fail(doc)

    def test_options_argument_in_usage(self):
        doc = """
        Usage: prog [options] --color <COLOR>

        Options:
            --color=<COLOR>
        """

        sys.argv = ['prog', '--color', 'red']
        self.eq(doc, {'--': False, '--color': 'red'})

        doc2 = """
        Usage: prog [options] -c <COLOR>

        Options:
            -c, --color=<COLOR>
        """
        self.eq(doc2, {'--': False, '--color': 'red', '-c': 'red'})

    def test_wrong_unknow_option_note(self):
        doc = '''Usage: prog --long'''
        with StdoutRedirect() as f:
            with self.assertRaises(SystemExit):
                docpie(doc, ['prog', '--long=s'])

        self.assertNotIn('Unknown option:', f.read())

    def test_cp_indent_not_work(self):
        doc = """Example for docpie, linux cp-like command


NAME
     cp -- copy files

USAGE:
     cp [options] <source_file> ... <target_directory>

OPTIONS:
     -f    If the destination file cannot be opened, remove it and create a
           new file, without prompting for confirmation regardless of its per-
           missions.
     -v, --verbose
           Cause cp to be verbose, showing files as they are copied.
     -X    Do not copy Extended Attributes (EAs) or resource forks.
     -R    If source_file designates a directory, cp copies the directory and
           the entire subtree connected at that point."""

        sys.argv = ['prog', 'source', 'target']
        self.eq(doc, {'--': False, '-f': False, '-v': False,
                      '--verbose': False, '-X': False, '-R': False,
                      '<source_file>': ['source'],
                      '<target_directory>': 'target'})

    def test_option_section_title(self):
        doc = """
        Usage: prog [options]

        OpTiOnS:
            -a
        Another OpTiOnS:
            -b
        """

        pie = Docpie(doc)
        opt_sections = pie.option_sections

        self.assertEqual(set(('', 'Another')), set(opt_sections))

    def test_long_option_with_same_prefix(self):
        doc = """
        Usage: prog --long
               prog --long-opt
        """
        sys.argv = ['prog', '--long-opt']
        self.eq(doc, {'--': False, '--long': False, '--long-opt': True})


        doc = """
        Usage: prog --long=<opt>
               prog --long-opt
        """
        sys.argv = ['prog', '--long-opt']
        self.eq(doc, {'--': False, '--long': None, '--long-opt': True})
        sys.argv = ['prog', '--long', 'opt']
        self.eq(doc, {'--': False, '--long': 'opt', '--long-opt': False})
        sys.argv = ['prog', '--long=opt']
        self.eq(doc, {'--': False, '--long': 'opt', '--long-opt': False})

    def test_raise_default_handler(self):
        doc = "Usage: prog"
        sys.argv = ['prog', 'extra']

        try:
            docpie(doc)
        except BaseException as e:
            self.assertEqual(str(e), "Usage: prog\n")
        else:
            raise RuntimeError('Should raise here')


class APITest(unittest.TestCase):

    def eq(self, result, doc, argv=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           auto2dashes=True, name=None, case_sensitive=False,
           optionsfirst=False, appearedonly=False, extra={}):

        pieargs = locals()
        pieargs.pop('self')
        pieargs.pop('result')

        self.assertEqual(docpie(**pieargs), result)

    def fail_(self, doc, argv=None, help=True, version=None,
              stdopt=True, attachopt=True, attachvalue=True,
              auto2dashes=True, name=None, case_sensitive=False,
              optionsfirst=False, appearedonly=False, extra={},
              exception=DocpieExit):
        pieargs = locals()
        pieargs.pop('self')
        pieargs.pop('exception')

        self.assertRaises(exception, docpie, **pieargs)

    def test_options_first(self):
        doc = 'Usage: prog [-a] cmd [<args>...]'

        self.eq(
            {'-a': True, '<args>': ['-a', '-aa', '--'], 'cmd': True,
             '--': False},
            doc, 'prog -a cmd -a -aa --', optionsfirst=True)

    def test_appeared_only(self):
        doc = '''
        Usage: [options] [-i] [-n]

        Options:
            -i, --in-option
        '''

        self.eq({'-n': True, '--': False},
                doc, 'prog -n', appearedonly=True)
        self.eq({'-i': True, '--in-option': True, '--': False},
                doc, 'prog -i', appearedonly=True)

        doc = '''
        Usage: [options]

        Options:
            -i --inside=[<sth>]
        '''
        self.eq({'--': False}, doc, '', appearedonly=True)

    def test_issue_4(self):
        # https://github.com/TylerTemp/docpie/issues/4
        doc = """
        Example of program which uses [options] shortcut in pattern.

        Usage:
          options_shortcut_example.py --help | --version
          options_shortcut_example.py [options] (do --after=<float> [--grace])... <port>...

        Arguments:
          <port>                   give port

        Generic options:
          -h --help                show this help message and exit
          --version                show version and exit
          -n, --number N           use N as a number
          -t, --timeout TIMEOUT    set timeout TIMEOUT seconds
          --apply                  apply changes to database
          -q                       operate in quiet mode

        Commands:
          do                       do smth

        Command options:
          --after=<float>          do smth after <float> time
          --grace                  do smth with grace
        """
        argv = ['options_shortcut_example.py', '-n', '6', 'do', '--after=4', 'a.txt']
        expect = {
            '--': False,
            '--after': ['4'],
            '--apply': False,
            '--grace': 0,
            '--help': False,
            '--number': '6',
            '--timeout': None,
            '--version': False,
            '-h': False,
            '-n': '6',
            '-q': False,
            '-t': None,
            '<port>': ['a.txt'],
            'do': 1}
        self.eq(expect, doc, argv)
        self.fail_(doc, argv, optionsfirst=True)

        doc2 = """
        Example of program which uses [options] shortcut in pattern.

        Usage:
          options_shortcut_example.py --help | --version
          options_shortcut_example.py [options] (do [--after=<float>] [--grace])... <port>...

        Arguments:
          <port>                   give port

        Generic options:
          -h --help                show this help message and exit
          --version                show version and exit
          -n, --number N           use N as a number
          -t, --timeout TIMEOUT    set timeout TIMEOUT seconds
          --apply                  apply changes to database
          -q                       operate in quiet mode

        Commands:
          do                       do smth

        Command options:
          --after=<float>          do smth after <float> time
          --grace                  do smth with grace
        """

        self.eq(expect, doc2, argv)
        # should NOT use optionsfirst here.
        except_options_first = {
            '--': False,
            '--after': [],
            '--apply': False,
            '--grace': 0,
            '--help': False,
            '--number': '6',
            '--timeout': None,
            '--version': False,
            '-h': False,
            '-n': '6',
            '-q': False,
            '-t': None,
            '<port>': ['--after=4', 'a.txt'],
            'do': 1
        }
        self.eq(except_options_first, doc2, argv, optionsfirst=True)

    def test_issue_4_real_reason(self):
        doc = """Usage: prog [options] [--want=<val2>] <arg>

        Options:
            -e, --expect=<val>"""

        argv = ['prog', '--expect=sth', 'arg']  # this won't fail
        expect = {'--': False, '--expect': 'sth', '-e': 'sth', '--want': None,
                  '<arg>': 'arg'}
        self.eq(expect, doc, argv)
        self.eq(expect, doc, argv, optionsfirst=True)

        argv = ['prog', '--expect', 'sth', 'arg']
        self.eq(expect, doc, argv, optionsfirst=True)
        # this will fail on 0.2.8
        argv = ['prog', '-e', 'sth', 'arg']
        self.eq(expect, doc, argv, optionsfirst=True)

        argv = ['prog', '--want', 'sth', 'arg']
        expect = {'--': False, '--expect': None, '-e': None, '--want': 'sth',
                  '<arg>': 'arg'}
        self.eq(expect, doc, argv, optionsfirst=True)

        doc = """Usage: prog [options] -w<val> <arg>"""
        argv = ['prog', '-w', 'sth', 'arg']
        expect = {'--': False, '-w': 'sth', '<arg>': 'arg'}
        # this will fail on 0.2.8
        self.eq(expect, doc, argv, optionsfirst=True)

        argv = ['prog', '-wsth', 'arg']
        self.eq(expect, doc, argv, optionsfirst=True)

    def test_extra_override_help(self):
        # with StderrRedirect() as f:
        sys.argv = ['prog', '-h']
        with self.assertRaises(SystemExit) as cm:
            docpie('Usage: prog [options]', help=True, extra={
                '-h': lambda pie, flag: sys.exit('exit')
            })

        exception = cm.exception
        self.assertEqual(exception.args[0], 'exit')


    def test_extra_override_version(self):
        # with StderrRedirect() as f:
        sys.argv = ['prog', '-v']
        with self.assertRaises(SystemExit) as cm:
            docpie('Usage: prog [options]', version='0.0.1', extra={
                '-v': lambda pie, flag: sys.exit('version~')
            })

        exception = cm.exception
        self.assertEqual(exception.args[0], 'version~')

    def test_new_help_default(self):
        """https://github.com/TylerTemp/docpie/issues/10"""
        doc = """
        Header
            Usage: prog [options]

            Options: -a
                     -b

            Some description
"""
        argv = ['prog', '-h']
        with StdoutRedirect() as f:
            with self.assertRaises(SystemExit) as cm:
                docpie(doc, help=True, argv=argv)

        stdout = f.read()
        self.assertIn('Some description', stdout)
        self.assertIn('Header', stdout)
        # self.assertEqual(doc, stdout)
        default_doc_style = """\
Header
    Usage: prog [options]

    Options: -a
             -b

    Some description
"""
        self.assertEqual(default_doc_style, stdout)
        # assert False, repr(stdout)

    def test_help_style_python(self):
        doc = """
        Header
            Usage: prog [options]

            Options: -a
                     -b

       Some description


    """
        argv = ['prog', '-h']
        with StdoutRedirect() as f:
            with self.assertRaises(SystemExit) as cm:
                docpie(doc, help=True, helpstyle='python', argv=argv)

        stdout = f.read()
        self.assertIn('Some description', stdout)
        self.assertIn('Header', stdout)
        # self.assertEqual(doc, stdout)
        python_style_doc = """\
 Header
     Usage: prog [options]

     Options: -a
              -b

Some description
"""
        self.assertEqual(python_style_doc, stdout)
        # assert False, repr(stdout)

    def test_help_style_dedent(self):
        doc = """
        Header
            Usage: prog [options]

            Options: -a
                     -b

         Some description

    """
        argv = ['prog', '-h']
        with StdoutRedirect() as f:
            with self.assertRaises(SystemExit) as cm:
                docpie(doc, help=True, helpstyle='dedent', argv=argv)

        stdout = f.read()
        self.assertIn('Some description', stdout)
        self.assertIn('Header', stdout)
        # self.assertEqual(doc, stdout)
        python_style_doc = """
Header
    Usage: prog [options]

    Options: -a
             -b

 Some description

"""
        self.assertEqual(python_style_doc, stdout)

class NewErrorTest(unittest.TestCase):

    def setUp(self):
        self.doc = """
        Usage:
            prog [options] --prefix=<args>...

        Options:
            --prepare
            -p, --prefix=<args>...
        """

    def with_raise(self, expection):
        with self.assertRaises(expection) as cm:
            docpie(self.doc)

        return cm.exception

    def test_unknown_long_option(self):
        sys.argv = ['prog', '--not-exists']
        error = self.with_raise(UnknownOptionExit)
        self.assertEqual('--not-exists', error.option)
        self.assertEqual('--not-exists', error.inside)

    def test_unknown_short_option(self):
        sys.argv = ['prog', '-not']
        error = self.with_raise(UnknownOptionExit)
        self.assertEqual('-n', error.option)
        self.assertEqual('-not', error.inside)

    def test_long_option_expect_args(self):
        sys.argv = ['prog', '--prefix']
        error = self.with_raise(ExpectArgumentExit)
        self.assertIn('--prefix', error.option)

    def test_short_option_expect_args(self):
        sys.argv = ['prog', '-p']
        error = self.with_raise(ExpectArgumentExit)
        self.assertIn('-p', error.option)

    def test_expect_no_args(self):
        sys.argv = ['prog', '--prepare=arg']
        error = self.with_raise(ExceptNoArgumentExit)
        self.assertIn('--prepare', error.option)
        self.assertEqual('arg', error.hit)

    def test_long_option_hit_double_dashes(self):
        sys.argv = ['prog', '--prefix', '--']
        error = self.with_raise(ExpectArgumentHitDoubleDashesExit)
        self.assertIn('--prefix', error.option)

    def test_short_option_hit_double_dashes(self):
        sys.argv = ['prog', '-p', '--']
        error = self.with_raise(ExpectArgumentHitDoubleDashesExit)
        self.assertIn('--prefix', error.option)

    def test_ambiguous_prefix(self):
        sys.argv = ['prog', '--pre']
        error = self.with_raise(AmbiguousPrefixExit)
        self.assertEqual('--pre', error.prefix)
        self.assertEqual(set(('--prepare', '--prefix')), set(error.ambiguous))


class IssueTest(unittest.TestCase):

    def test_issue_5(self):
        """https://github.com/TylerTemp/docpie/issues/5"""
        sys.argv = ['prog', '--bb', 'B', '--cc', 'C']
        doc = '''Usage: pie.py [--aa=AA|--bb=BB] --cc=CC'''
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, '--aa': None, '--bb': 'B', '--cc': 'C'})

        sys.argv = ['prog', '--aa', 'A', '--cc', 'C']
        doc = '''Usage: pie.py [--aa=AA|--bb=BB] --cc=CC'''
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, '--aa': 'A', '--bb': None, '--cc': 'C'})

    def test_issue_6(self):
        """https://github.com/TylerTemp/docpie/issues/6"""
        doc = '''usage: pie.py [--aa=AA|[--bb=BB | --cc=CC]]'''
        sys.argv = ['prog']
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, '--aa': None, '--bb': None, '--cc': None})

        sys.argv = ['prog', '--aa', 'VA']
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, '--aa': 'VA', '--bb': None, '--cc': None})

        sys.argv = ['prog', '--bb', 'VB']
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, '--aa': None, '--bb': 'VB', '--cc': None})


        sys.argv = ['prog', '--cc=VC']
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, '--aa': None, '--bb': None, '--cc': 'VC'})

        sys.argv = ['prog', '--aa=VA', '--bb', 'VB']
        self.assertRaises(DocpieExit, docpie, doc)

        sys.argv = ['prog', '--aa=VA', '--cc', 'VC']
        self.assertRaises(DocpieExit, docpie, doc)

        sys.argv = ['prog', '--bb=VB', '--cc', 'VC']
        self.assertRaises(DocpieExit, docpie, doc)

        doc = """Usage: prog [a | [b | [c | [d | e]]]]"""
        sys.argv = ['prog']
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, 'a': False, 'b': False, 'c': False, 'd': False, 'e': False})

        doc = """Usage: prog [a | [b | [c | [d | e]]]]"""
        sys.argv = ['prog', 'd']
        pie = docpie(doc)
        self.assertEqual(pie, {'--': False, 'a': False, 'b': False, 'c': False, 'd': True, 'e': False})

        doc = """Usage: prog [a | [b | [c | [d | e]]]]"""
        sys.argv = ['prog', 'b', 'd']
        self.assertRaises(DocpieExit, docpie, doc)

    def test_issue_12(self):
        """https://github.com/TylerTemp/docpie/issues/12"""
        doc = """Usage: prog [a]..."""
        sys.argv = ['prog']
        pie = docpie(doc, appearedonly=True)
        self.assertEqual(pie, {'--': False})

        doc = """Usage: prog [-a]..."""
        sys.argv = ['prog']
        pie = docpie(doc, appearedonly=True)
        self.assertEqual(pie, {'--': False})

        doc = """Usage: prog [<a>]..."""
        sys.argv = ['prog']
        pie = docpie(doc, appearedonly=True)
        self.assertEqual(pie, {'--': False})

        doc = """Usage: prog [<a>]..."""
        sys.argv = ['prog']
        pie = docpie(doc, appearedonly=False)
        self.assertNotEqual(pie, {'--': False})

        doc = """Usage: prog [[-a]...]"""
        sys.argv = ['prog']
        pie = docpie(doc, appearedonly=True)
        self.assertEqual(pie, {'--': False})

        doc = """Usage:
            create [--vbf_version=VBFVERSION]
                   [--description=DESCRIPTION]...
                   [--parameter_settings=(PARAMETER PARAMETERVALUE)]
                   [([--vbt_sort | --vbt_last] --sign=ADDRESS)]
        """
        sys.argv = ['prog', '--sign=0x00', '--vbt_last']
        pie = docpie(doc, appearedonly=True)
        self.assertEqual(pie, {'--': False,
         '--sign': '0x00',
         '--vbt_last': True})

class Writer(StringIO):

    if sys.hexversion >= 0x03000000:
        def u(self, string):
            return string
    else:
        def u(self, string):
            return unicode(string)

    def write(self, string):
        return super(Writer, self).write(self.u(string))


class StdoutRedirect(object):
    fake_out = Writer()

    def __enter__(self):
        self.fake_out.seek(0)
        self.fake_out.truncate()
        self.real_out = sys.stdout
        sys.stdout = self.fake_out
        return self.fake_out

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fake_out.seek(0)
        sys.stdout = self.real_out
        return False


class StderrRedirect(object):
    fake_err = Writer()

    def __enter__(self):
        self.fake_err.seek(0)
        self.fake_err.truncate()
        self.real_err = sys.stderr
        sys.stderr = self.fake_err
        return self.fake_err

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fake_err.seek(0)
        sys.stderr = self.real_err
        return False


def case():
    return (
        unittest.TestLoader().loadTestsFromTestCase(BasicTest),
        unittest.TestLoader().loadTestsFromTestCase(RunDefaultTest),
        unittest.TestLoader().loadTestsFromTestCase(APITest),
        unittest.TestLoader().loadTestsFromTestCase(NewErrorTest),
        unittest.TestLoader().loadTestsFromTestCase(IssueTest),
    )


def suite():
    return unittest.TestSuite(case())


def main():
    unittest.TextTestRunner().run(suite())


if __name__ == '__main__':
    # bashlog.stdoutlogger(None, bashlog.DEBUG, True)
    # unittest.main()
    main()
