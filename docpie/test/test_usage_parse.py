import unittest
import logging

from docpie import bashlog
from docpie.parser import UsageParser
from docpie.element import OptionsShortcut
from docpie.element import Either
from docpie.element import Option, Command, Argument
from docpie.element import Optional, Required

logger = logging.getLogger('docpie.test.usage')


class UsageParserTest(unittest.TestCase):

    def eq(self, txt, *obj, **kwargs):
        name = kwargs.get('name', None)
        parsed = []
        for each in UsageParser(txt, name, True)._chain:
            parsed.append([x.fix() for x in each])
        self.assertEqual(parsed, list(obj))

    def test_nest_brancket(self):
        self.assertEqual(Required(Command(''), repeat=True),
                         Required(Required(Required(Command(''))),
                                  repeat=True).fix())
        self.assertEqual(Optional(Command(''), repeat=True),
                         Required(Optional(Required(Command(''))),
                                  repeat=True).fix())

    def test_bare(self):
        self.eq('app', [])
        self.eq('app here', [], name='here')

    def test_dot(self):
        doc = 'app cmd...'
        self.eq(doc, [Required(Command('cmd'), repeat=True)])

    def test_wrongflag_no_bracket(self):
        doc = 'app --no-brancket=sth'
        self.eq(doc, [Command('--no-brancket=sth')])

    def test_wrongflag_symbol(self):
        doc = '''\
        app --2-eq==<sth>
        app --2-eq=><sth>
        app --2-eq=~<sth>'''
        self.eq(doc,
                [Command('--2-eq==<sth>')],
                [Command('--2-eq=><sth>')],
                [Command('--2-eq=~<sth>')],
                )

    def test_arg_with_space(self):
        self.eq('app --has-space=<    >',
                [Option('--has-space', ref=Required(Argument('<    >')))])

    def test_wrongflag_not_format(self):
        self.eq('app --not-in-format=<arg>here',
                [Command('--not-in-format=<arg>here')])

    def test_eq_symbol_cmd(self):
        self.eq('app equal = <test>',
                [Command('equal'), Command('='), Argument('<test>')])

    def test_option_args_dots(self):
        self.eq('app -a <here>... <there>',
                [Option('-a'),
                 Required(Argument('<here>'), repeat=True),
                 Argument('<there>')])

    def test_non_options_space(self):
        self.eq('app [options] [ options ] [ options] [options ]',
                [OptionsShortcut(), Optional(Command('options')),
                 Optional(Command('options')), Optional(Command('options'))])

    def test_non_options(self):
        self.eq('app [options]... (options) [options...]',
                [Optional(OptionsShortcut(), repeat=True),
                 Required(Command('options')),
                 Optional(Command('options'), repeat=True)])

    def test_unstd_arg(self):
        self.eq('app [options] install <,>',
                [OptionsShortcut(), Command('install'), Argument('<,>')])

    def test_multi_cmd(self):
        self.eq('app [go go]', [Optional(Command('go'), Command('go'))])

    def test_multi_cmd_dot(self):
        self.eq('app [go go]...',
                [Optional(Command('go'), Command('go'), repeat=True)])

    def test_flag_eq_arg_in_brancket(self):
        self.eq('app [--hello=<world>]',
                [Optional(
                    Option('--hello', ref=Required(Argument('<world>')))
                )])

    def test_multi_option(self):
        self.eq('app [-v -v]',
                [Optional(Option('-v'), Option('-v'))])

    def test_option_dot(self):
        self.eq('app -v ...',
                [Required(Option('-v'), repeat=True)])

    def test_auto_fix_nest_brancket(self):
        self.eq('app [(-a -b)]',
                [Optional(Option('-a'), Option('-b'))])

    def test_auto_fix_nest_brancket(self):
        self.eq('app [<n> [<n>...]]',
                [Optional(Argument('<n>'),
                 Optional(Argument('<n>'), repeat=True))])

    def test_arg_with_colon(self):
        self.eq('app [-a <host:port>]',
                [Optional(Option('-a'), Argument('<host:port>'))])

    def test_arg_with_slash(self):
        self.eq('app go <d> --sp=<km/h>',
                [Command('go'), Argument('<d>'),
                 Option('--sp', ref=Required(Argument('<km/h>')))
                ]
        )

    def test_pipe_count(self):
        self.eq(
            'app [-v | -vv | -vvv]',
            [Optional(
                Either(
                    Required(Option('-v')),
                    Required(Option('-v'), Option('-v')),
                    Required(Option('-v'), Option('-v'), Option('-v')),
                )
            )]
        )

    def test_pipe_option_with_arg(self):
        self.eq(
            'app (<sth> --all|<else>)',
            [Required(
                Either(
                    Required(Argument('<sth>'), Option('--all')),
                    Required(Argument('<else>')),
                )
            )]
        )

    def test_pipe_arg_with_option(self):
        self.eq(
            'app [<n>|--fl <n>]',
            [Optional(
                Either(
                    Required(Argument('<n>')),
                    Required(Option('--fl'), Argument('<n>')),
                )
            )]
        )

    def test_pipe_with_eq(self):
        self.eq(
            'app (--xx=<x>|--yy=<y>)',
            [Required(
                Either(
                    Required(Option('--xx', ref=Required(Argument('<x>')))),
                    Required(Option('--yy', ref=Required(Argument('<y>')))),
                )
            )]
        )

    def test_pipe_nest(self):
        self.eq(
            'app [(-v | -vv) | -vvv]',
            [Optional(
                Either(
                    Required(
                        Either(
                            Required(Option('-v')),
                            Required(Option('-v'), Option('-v')),
                        )
                    ),
                    Required(Option('-v'), Option('-v'), Option('-v'))
                )
            )]
        )

    def test_pipe_args(self):
        self.eq('app [<arg1> | ARG2 | <arg3>]',
                [Optional(Argument('<arg1>', 'ARG2', '<arg3>'))])

    def test_pipe_args_with_bracket(self):
        self.eq('app ((<arg1> | ARG2) | <arg3>)',
                [Required(Argument('<arg1>', 'ARG2', '<arg3>'))])

    def test_pipe_not_args(self):
        self.eq('app ((-t | --test) | <arg>)',
                [Required(
                    Either(
                        Required(Either(Required(Option('-t')),
                                        Required(Option('--test')))),
                        Required(Argument('<arg>'))
                    )
                )])


def suite():
    return unittest.TestSuite(case())


def case():
    return (unittest.TestLoader().loadTestsFromTestCase(UsageParserTest),)

if __name__ == '__main__':
    # getlogger('docpie', DEBUG)
    unittest.TextTestRunner().run(suite())
