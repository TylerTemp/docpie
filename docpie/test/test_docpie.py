# coding: utf-8
import unittest
import logging
import sys

from docpie import bashlog
from docpie import docpie
from docpie.error import DocpieExit, DocpieError

logger = logging.getLogger('docpie.test.docpie')


class DocpieBasicTest(unittest.TestCase):

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

        # Note: different from docpie
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

        self.assertRaises(DocpieExit, docpie, doc, 'prog -v')
        #
        self.assertRaises(DocpieExit, docpie, doc,
                          'prog -v input.py output.py')
        self.assertRaises(DocpieExit, docpie, doc, 'prog --fake')
        self.assertRaises(DocpieExit, docpie, doc, 'prog --hel')

    def test_command_help(self):

        # Temp disable output
        class EmptyWriter(object):
            def write(self, *a, **k):
                pass

        real_stdout, sys.stdout = sys.stdout, EmptyWriter()

        doc = 'usage: prog --help-commands | --help'
        self.assertRaises(SystemExit, docpie, doc, 'prog --help')

        sys.stdout = real_stdout

    # def test_unicode(self):
    #     try:
    #         doc = u'usage: prog [-o <呵呵>]'
    #     except SyntaxError:
    #         pass
    #     else:
    #         self.assertEqual(
    #             docpie(doc, u'prog -o 嘿嘿'), {'-o': True, u'<呵呵>': u'嘿嘿',
    #                                          '--': False})

    def test_count_multiple_flags(self):
        eq = self.assertEqual
        eq(docpie('usage: prog [-vv]', 'prog'),
           {'-v': 0, '--': False})
        eq(docpie('usage: prog [-v]', 'prog -v'),
           {'-v': True, '--': False})
        self.assertRaises(DocpieExit, docpie, 'usage: prog [-vv]', 'prog -v')
        eq(docpie('usage: prog [-vv]', 'prog -vv'),
           {'-v': 2, '--': False})
        # Note it's different from docpie
        self.assertRaises(
            DocpieExit, docpie, 'usage: prog [-v | -vv | -vvv]', 'prog -vvv')
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
                 Options:\n\t-d --data=<arg>    Input data [default: x]
              '''
        eq(docpie(doc, 'prog'), {'--data': ['x'], '-d': ['x'],
                                 '--': False})

        doc = '''Usage: prog [--data=<data>...]\n
                 Options:\n\t-d --data=<arg>    Input data [default: x y]
              '''
        eq(docpie(doc, 'prog'), {'--data': ['x', 'y'], '-d': ['x', 'y'],
                                 '--': False})

        doc = '''Usage: prog [--data=<data>...]\n
                 Options:\n\t-d --data=<arg>    Input data [default: x y]
              '''
        eq(docpie(doc, 'prog --data=this'),
           {'--data': ['this'], '-d': ['this'], '--': False})

    def test_to_fix_this(self):
        eq = self.assertEqual
        # this WON'T work:
        self.assertRaises(DocpieExit, docpie,
                          'usage: prog --long=<a>', 'prog --long=')
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


class DocpieRunDefaultTest(unittest.TestCase):

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

        # Note: different from docopt, docpie doesn't support this so far
        sys.argv = ['prog', '--ver']
        self.fail(doc)

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

        # Note: different from docopt
        sys.argv = ['prog', '--pa=home/']
        self.fail(doc)

        # Note: different from docopt
        sys.argv = ['prog', '--pa', 'home/']
        self.fail(doc)

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

        # Not support so far
        sys.argv = ['prog', '--verb']
        self.fail(doc)

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

        # Note: defferent from docopt
        # that you can't write as `-armMSG` or `-armmsg`
        doc = '''usage: prog [-armmesg]

options: -a        Add
         -r        Remote
         -m <msg>  Message
'''
        self.fail(doc, exception=DocpieError)

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

        # Note: different from docopt
        # that `<name>` & `<type>` should both present or omit
        sys.argv = ['prog', '10', '20']
        self.fail(doc)

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

        # Note: different from docopt
        # that once `<kind>` is perfectly matched, docpie will not try the
        # branch `<name> <type>`
        sys.argv = ['prog', '10', '20']
        self.fail(doc)

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

        # Different from docopt:
        # `<name>` should appear even time(s)
        sys.argv = ['prog', '10']
        self.fail(doc)

        sys.argv = ['prog']
        self.eq(doc, {'<name>': [], '--': False})

        # But you can write in this way
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

    # This is not supported so far
    # r"""usage: prog --long=<arg> ..."""
    #
    # $ prog --long one
    # {"--long": ["one"]}
    #
    # $ prog --long one --long two
    # {"--long": ["one", "two"]}

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
          --input=<file name>...'''

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
        # Not support in docpie
        # r"""Usage: prog [options]
        #
        # global options: --foo
        # local options: --baz
        #                --bar
        # other options:
        #  --egg
        #  --spam
        # -not-an-option-
        #
        # """
        # $ prog --baz --egg
        # {"--foo": false, "--baz": true, "--bar": false,
        # "--egg": true, "--spam": false}
        pass

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


def case():
    return (unittest.TestLoader().loadTestsFromTestCase(DocpieBasicTest),
            unittest.TestLoader().loadTestsFromTestCase(DocpieRunDefaultTest))


def suite():
    return unittest.TestSuite(case())


def main():
    unittest.TextTestRunner().run(suite())

if __name__ == '__main__':
    # bashlog.stdoutlogger(None, bashlog.DEBUG, True)
    logging.getLogger().setLevel(bashlog.ERROR)
    main()
