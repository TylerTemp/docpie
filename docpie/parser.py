from docpie.element import Atom, Option, Command, Argument
from docpie.element import Optional, Required, OptionsShortcut
from docpie.element import Either
from docpie.tokens import Token
from docpie.error import DocpieError

import logging
import re

logger = logging.getLogger('docpie.parser')


class Parser(object):

    section_re_str = (r'(?:^|\n)'
                      r'(?P<name>[\ \t]*{0}[\ \t]*)'
                      r'(?P<sep>\n?)'
                      r'(?P<section>.*?)'
                      r'\s*'
                      r'(?:\n\s*\n|\n\s*$|$)')

    @classmethod
    def _parse_pattern(klass, token):
        elements = []
        while token:
            atom = token.current()
            if atom in ('(', '['):
                elements.append(klass._parse_bracket(token))
            elif atom == '|':
                elements.append(token.next())
            else:
                assert atom != '...', 'fix me: unexpected "..." when parsing'
                elements.extend(klass._parse_element(token))

        logger.debug(elements)
        if '|' in elements:
            elements[:] = [klass._parse_pipe(elements)]
        return elements

    @classmethod
    def _parse_bracket(cls, token):
        elements = []
        start = token.next()
        instance_type = Required if start == '(' else Optional

        lis = token.till_end_bracket(start)

        repeat = False
        while token.current() == '...':
            repeat = True
            token.next()

        bracket_token = Token(lis)

        instances = cls._parse_pattern(bracket_token)

        # Not support on py2.5
        # return instance_type(*instances, repeat=repeat)
        return instance_type(*instances, **{'repeat': repeat})


    @classmethod
    def _parse_element(cls, token):
        atom = token.next()
        assert atom is not None
        if atom == '[options]':
            # `[options] ...`? Note `[options...]` won't work
            repeat = False
            while token and token.current() == '...':
                repeat = True
                token.next()
            if repeat:
                ins = Optional(OptionsShortcut(), repeat=True)
            else:
                ins = OptionsShortcut()
            return (ins,)
        atom_class = Atom.get_class(atom)
        if (atom_class is Option and
                not atom.startswith('--') and
                len(atom) > 2 and
                Atom.stdopt):
            ins_lis = [Option('-' + short) for short in atom[1:]]
        else:
            ins_lis = [atom_class(atom)]
        if token.current() == '...':
            token.next()
            # Not work on py2.6
            # ins = Required(*ins_lis, repeat=True)
            ins = Required(*ins_lis, **{'repeat': True})
            while token.current() == '...':
                token.next()
            return (ins,)
        return ins_lis

    @classmethod
    def _parse_pipe(klass, lis):
        assert '...' not in lis
        assert len(lis) >= 3
        assert lis[0] != '|' != lis[-1]
        # assert lis[0] != '|'    # don't use lis[0] != lis[-1] != '|'
        # assert lis[-1] != '|'
        groups = [Required()]
        for each in lis:
            if each == '|':
                groups.append(Required())
            else:
                groups[-1].append(each)

        return Either(*groups)

    @classmethod
    def fix(cls, opts, usages):
        # check if same option announced twice in Options
        opt_2_ins = {}
        for opt in opts:
            names = opt.get_names()
            for name in names:
                if name in opt_2_ins:
                    logger.critical('name: %s, opt_2_ins: %s', name, opt_2_ins)
                    raise DocpieError('%s announced more than once '
                                      'in Options' % name)
                opt_2_ins[name] = opt
        # set the option shortcut
        OptionsShortcut.set_ref(opts)

        for usage in usages:
            if usage is not None:
                usage.fix_optional(opt_2_ins)
                opts_in_usage, shortcuts = \
                    cls.find_option_names_no_shortcut_and_shortcut(usage)
                if opts_in_usage and shortcuts:
                    for cut in shortcuts:
                        cut.set_hide(opts_in_usage)

        return opts, usages

    @classmethod
    def find_option_names_no_shortcut_and_shortcut(cls, element):
        shortcuts = []
        result = set()
        if isinstance(element, OptionsShortcut):
            shortcuts.append(element)
        elif isinstance(element, list):
            for each in element:
                names, srtcuts = \
                    cls.find_option_names_no_shortcut_and_shortcut(each)
                result.update(names)
                shortcuts.extend(srtcuts)
        elif isinstance(element, Option):
            result.update(element._names)
        else:
            pass

        return result, shortcuts

    @classmethod
    def parse_section(cls, text, name, case_sensitive=False):
        section_re = re.compile(
            cls.section_re_str.format(name),
            flags=re.DOTALL | (0 if case_sensitive else re.IGNORECASE))
        match = section_re.search(text)
        if match is None:
            return None
        dic = match.groupdict()
        logger.debug(dic)
        if dic['sep'] == '\n':
            return dic['section']
        reallen = len(dic['name'])
        replace = ''.ljust(reallen)
        drop_name = match.expand('%s\g<sep>\g<section>' % replace)
        return cls.drop_started_empty_lines(drop_name).rstrip()

    @staticmethod
    def drop_started_empty_lines(text):
        # drop the empty lines at start
        # different from lstrip
        logger.debug(text)
        lis = text.splitlines()
        while lis and not lis[0].strip():
            lis.pop(0)

        return '\n'.join(lis)

class OptionParser(Parser):
    split_re = re.compile(r'(<.*?>)|\s+')
    wrap_symbol_re = re.compile(r'([\|\[\]\(\)]|\.\.\.)')
    line_re = re.compile(r'^(?P<indent> *)'
                         r'(?P<option>[\d\w=_, <>\-\[\]\.]+?)'
                         r'(?P<separater>$| $| {2,})'
                         r'(?P<description>.*?)'
                         r' *$',
                         flags=re.IGNORECASE)
    indent_re = re.compile(r'^(?P<indent> *)')
    to_space_re = re.compile(r',\s?|=')

    # split_re = re.compile(r'(<.*?>)|\s?')
    # default ::= chars "[default: " chars "]"
    # support xxxxxx.[default: ]
    # support xxxxxx.[default: yes]
    # not support xxxxx[default: no].
    # not support xxxxx[default: no]!
    # not support xxxxxx.[default: no ]
    # If you want to match a not so strict format, this may help:
    # default_re = re.compile(r'\[default: *(?P<default>.*?) *\]'
    #                         r' *'
    #                         r'[\.\?\!]? *$',
    #                         flags=re.IGNORECASE)
    default_re = re.compile(r'\[default: (?P<default>.*?)\] *$',
                            flags=re.IGNORECASE)

    def __init__(self, text=None):
        self.text = text
        if self.text is None or not self.text.strip():    # empty
            self._opt_and_default_str = []
        else:
            self._opt_and_default_str = list(self._parse_text(self.text))

        self._chain = self._parse_to_instance(self._opt_and_default_str)

    def get_chain(self):
        return self._chain

    @classmethod
    def _parse_text(klass, text):
        collect = []
        to_list = text.splitlines()

        # parse first line. Should NEVER failed.
        # this will ensure in `[default: xxx]`,
        # the `xxx`(e.g: `\t`, `,`) will not be changed by _format_line
        previous_line = to_list.pop(0)
        collect.append(klass._parse_line(previous_line))

        for line in to_list:
            indent_match = klass.indent_re.match(line)
            this_indent = len(indent_match.groupdict()['indent'])

            if this_indent >= collect[-1]['indent']:
                # A multi line description
                previous_line = line
                continue

            # new option line
            # deal the default for previous option
            collect[-1]['default'] = klass._parse_default(previous_line)
            # deal this option
            collect.append(klass._parse_line(line))
            logger.debug(collect[-1])
            previous_line = line
        else:
            collect[-1]['default'] = klass._parse_default(previous_line)

        return ((each['option'], each['default']) for each in collect)

    spaces_re = re.compile(r'(\ \ \s*|\t\s*)')

    @classmethod
    def _cut_first_spaces_outside_bracket(klass, string):
        right = klass.spaces_re.split(string)
        left = []
        if right and right[0] == '':    # re matches the start of the string
            right.pop(0)
        if right and not right[0].strip():    # it is indent
            left.append(right.pop(0))
        brackets = {'(': 0, '[': 0, '<': 0}
        close_brancket = {'(': ')', '[': ']', '<': '>'}
        cutted = ''

        while right:
            this = right.pop(0)
            for open_b in brackets:
                brackets[open_b] += this.count(open_b)
                brackets[open_b] -= this.count(close_brancket[open_b])
            if sum(brackets.values()):
                left.append(this)
            elif (not this.strip() and
                    len(this.expandtabs()) >= 2):
                cutted = this
                break
            else:
                left.append(this)
        return ''.join(left), cutted, ''.join(right)

    @classmethod
    def _parse_line(klass, line):
        opt_str, separater, description_str = \
                klass._cut_first_spaces_outside_bracket(line)

        logger.debug('%(line)s -> %(opt_str)r, '
                     '%(separater)r, '
                     '%(description_str)r' % locals())
        if description_str.strip():
            indent = len(opt_str.expandtabs()) + len(separater.expandtabs())
        else:
            indent = 2 + len(
                             klass.indent_re.match(
                                 opt_str.expandtabs()
                             ).groupdict()['indent'])
        return {'option': opt_str.strip(), 'indent': indent}

    @classmethod
    def _parse_default(klass, line):
        m = klass.default_re.search(line)
        if m is None:
            return None
        return m.groupdict()['default']

    @classmethod
    def _parse_to_instance(klass, lis):
        opts = []
        for opt_str, default in lis:
            logger.debug('%s:%r' % (opt_str, default))
            opt = klass._parse_opt_str(opt_str)
            opt.set_default(default)
            opts.append(opt)
        return opts

    @classmethod
    def _split_short_by_cfg(klass, s):
        if Atom.stdopt:
            if (not s.startswith('--') and
                    len(s) > 1):
                return s[:2], s[2:]
        return (s, '')

    @classmethod
    def _parse_opt_str(klass, opt):
        # -sth=<goes> ON -> -sth, <goes>, ON
        opt_lis = klass._opt_str_to_list(opt)
        logger.debug('%r -> %s' % (opt, opt_lis))

        first = opt_lis.pop(0)
        if not first.startswith('-'):
            raise DocpieError('option %s does not start with "-"' % first)

        # if Atom.stdopt:
        # -sth -> name=-s, value=sth
        # else:
        # -sth -> name=-sth, value=''
        name, value = klass._split_short_by_cfg(first)
        opt_ins = Option(name)
        if value:
            args_ins = [Required(Argument(value))]
        else:
            args_ins = []
        args = []    # store the current args after option
        for each in opt_lis:
            if each.startswith('-'):    # alias
                name, value = klass._split_short_by_cfg(each)
                opt_ins.set_alias(name)
                if value:
                    args_ins.append(Required(Argument(value)))
                if args:    # trun it into instance
                    this_arg = Required(
                                        *klass._parse_pattern(Token(args))
                                       ).fix()
                    if this_arg is not None:
                        args_ins.append(this_arg)
                del args[:]
            else:
                args.append(each)
        else:
            if args:    # trun it into instance
                this_arg = Required(*klass._parse_pattern(Token(args))).fix()
                if this_arg is not None:
                    args_ins.append(this_arg)

        # option without any args
        if not args_ins:
            return opt_ins

        # in Option, there should only have one arg list
        # e.g.: -f <file> --file=FILE -> -f/--file (<file>|FILE)
        # because the arg name will now be shown, it parsed as:
        # -f <file> --file=FILE -> -f/--file (<file>)
        current_ins = args_ins.pop(0)
        current_range = current_ins.arg_range()

        # avoid e.g.: -f <a> <b> --file <c>
        for other_ins in args_ins:
            this_range = other_ins.arg_range()
            if this_range != current_range:
                raise DocpieError("%s announced differently (%s, %s)" % (
                                  opt_ins, this_range, current_range))

        if len(current_range) > 1:
            logger.warning('too many possibilities: '
                           'option %s expect %s arguments',
                           name, '/'.join(map(str, current_range)))

        # TODO: check if current_ins contain Command(not allowed in fact)
        opt_ins.ref = current_ins
        return opt_ins

    @classmethod
    def _opt_str_to_list(klass, opt):
        dropped_comma_and_equal = opt.replace(',', ' ').replace('=', ' ')
        wrapped_space = klass.wrap_symbol_re.sub(
                                                 r' \1 ',
                                                 dropped_comma_and_equal
                                                )
        opt_lis = [x for x in klass.split_re.split(wrapped_space) if x]
        return opt_lis


class UsageParser(Parser):

    wrap_symbol_re = re.compile(r'(\[options\]|\.\.\.|\||\[|\]|\(|\))')
    split_re = re.compile(r'(\[options\]|\S*<.*?>\S*)|\s+')
    # will match '-', '--', and
    # flag ::= "-" [ "-" ] chars "=<" chars ">"
    # it will also match '---flag', so use startswith('---') to check
    std_flag_eq_arg_re = re.compile(r'(?P<flag>^-{1,2}[\da-zA-Z_\-]*)'
                                    r'='
                                    r'(?P<arg><.*?>)'
                                    r'$')

    def __init__(self, text=None, name=None):
        self.text = text
        self._chain = self._parse_text(self.text, name)

    @classmethod
    def _parse_text(klass, text, name):
        result = []
        for each_line in klass._split_line_by_indent(text):
            raw_str_lis = klass._parse_line_to_lis(each_line, name)
            chain = klass._parse_pattern(Token(raw_str_lis))
            result.append(chain)
        return result

    indent_re = re.compile(r'^ *')

    @classmethod
    def _split_line_by_indent(klass, text):
        lines = text.splitlines()
        if len(lines) == 1:
            yield lines[0]
            return

        first_line = lines.pop(0)
        line_to_join = [first_line]
        indent = len(
            klass.indent_re.match(first_line.expandtabs()).group())
        while lines:
            this_line = lines.pop(0)
            this_indent = len(
                klass.indent_re.match(this_line.expandtabs()).group())

            if this_indent > indent:
                line_to_join.append(this_line)
            else:
                yield ''.join(line_to_join)
                line_to_join[:] = (this_line,)
                indent = len(
                    klass.indent_re.match(this_line.expandtabs()).group())

        else:
            yield ' '.join(line_to_join)

    @classmethod
    def _parse_line_to_lis(klass, line, name=None):
        wrapped_space = klass.wrap_symbol_re.sub(r' \1 ', line.strip())
        logger.debug(wrapped_space)
        sepa_to_iter = (x for x in klass.split_re.split(wrapped_space) if x)
        result = []

        for atom in sepa_to_iter:
            if atom.startswith('-') and '=' in atom:
                result.extend(klass._format_flag_with_eq(atom))
            else:
                result.append(atom)

        # drop name
        if name is None:
            result.pop(0)
        else:
            if name not in result:
                raise DocpieError('%s is not in usage pattern %s' % (name,
                                                                     line))
            result[:] = result[result.index(name) + 1:]

        return result

    @classmethod
    def _format_flag_with_eq(klass, flag):
        if not flag.startswith('---'):
            match = klass.std_flag_eq_arg_re.match(flag)
            if match:
                mdic = match.groupdict()
                return (mdic['flag'], mdic['arg'])
        return (flag,)    # it's a strange-format command

    def get_chain(self):
        # if not self._chain:
        #     return [None]

        return [Required(*x).fix() for x in self._chain]


if __name__ == '__main__':
    from bashlog import getlogger
    from pprint import pprint
    getlogger('docpie', logging.DEBUG)

    doc = '''\
    --test [<a>|<b>|<c> <d>]
    --first  [default: \t]
    -f --file  nothing
    -v,--verbose\tstill nothing
    --multi=<test>
       Yes, default goes
       here. [default:  ]
    -pmsg, --print <msg>     -pmsg will not separated to -p <msg>[default: yes]
    -A --all=<list>  here
                     we are
                     [default: ,]
    -w<work> --work<work>
    --more=[<more1>, <more2>]...
    -T, --tab=<\t>, <    >  [default: \t]
    --test1 (<test>, [<test>], [<test>, <test>])...
    --test2 -t [<test> <test>...]
    -s
    --single'''

    # doc = '''\
    # --test2 -t [<test> <test>]...'''
    # doc = '''\
    # -test -t <arg>  sth'''
    parsed = OptionParser(doc)
    option_list = parsed.get_chain()
    # pprint(option_list)
    pprint([str(x) for x in option_list])

    doc = '''\
    app
    app ---what
    app - --
    app --more [<first> <second>]
    app cmd...
    app bad-flag --no-brancket=sth
    app bad-flag --2-eq==<sth>
    app strange-args --has-space=<    >
    app bad-flag --not-in-format=< >here
    app equal = <test>
    app -a <here>... <there>
    app [options] [ options ] [ options] [options ]
    app [options]... (options) [options...]
    app [options] install <,>
    app [-v | -vv | -vvv]
    app [go go]
    app [go go]...
    app [--hello=<world>]
    app [-v -v]
    app -v ...
    app [(-a -b)]
    app (<sth> --all|<else>)
    app [<n>|--fl <n>]
    app [<n> [<n>...]]
    app [-a <host:port>]
    app go <d> --sp=<km/h>
    app (--xx=<x>|--yy=<y>)
    app [--input=<file name>]
    app [(-v | -vv) | -vvv]
    app -msg...
    app ARG... ARG'''
    # Atom.stdopt = False
    x = UsageParser(doc, name='app')
    usage_list = x.get_chain()

    usage, option = Parser.fix(option_list, usage_list)

    print('Usage:')
    pprint([str(x) for x in option])
    print('\nOptions:')
    pprint([str(x) for x in usage])

    print('\n\n-------------------')
    print('Usage:')
    pprint([repr(x) for x in option])
    print('\nOptions:')
    pprint([repr(x) for x in usage])

    doc = '''\
    app [-a | (-a) -a | -aaa (-a) -a]'''

    parsed = UsageParser(doc)
    chain = parsed.get_chain()
    print(chain)

    # print()
    # for each_line in x._chain:
    #     if(each_line):
    #         pprint([str(x.fix()) for x in each_line])
    #     else:
    #         print([])
