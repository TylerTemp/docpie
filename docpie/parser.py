from docpie.element import Atom, Option, Command, Argument
from docpie.element import Optional, Required, OptionsShortcut
from docpie.element import Either
from docpie.token import Token
from docpie.error import DocpieError

import logging
import re

logger = logging.getLogger('docpie.parser')


class Parser(object):

    section_re_str = (r'(?:^|\n)'
                      r'(?P<raw>'
                      r'(?P<name>[\ \t]*{0}[\ \t]*)'
                      r'(?P<sep>\n?)'
                      r'(?P<section>.*?)'
                      r')'
                      r'\s*'
                      r'(?:\n\s*\n|\n\s*$|$)')

    def _parse_pattern(self, token):
        logger.debug('get token %s', token)
        elements = []
        while token:
            atom = token.current()
            if atom in ('(', '['):
                elements.append(self._parse_bracket(token))
            elif atom == '|':
                elements.append(token.next())
            else:
                assert atom != '...', 'fix me: unexpected "..." when parsing'
                elements.extend(self._parse_element(token))

        logger.debug(elements)
        if '|' in elements:
            elements[:] = [self._parse_pipe(elements)]
        logger.debug('parsed result %s', elements)
        return elements

    def _parse_bracket(self, token):
        elements = []
        start = token.next()
        instance_type = Required if start == '(' else Optional

        lis = token.till_end_bracket(start)

        repeat = False
        while token.current() == '...':
            repeat = True
            token.next()

        bracket_token = Token(lis)

        instances = self._parse_pattern(bracket_token)

        # Not support on py2.5
        # return instance_type(*instances, repeat=repeat)
        return instance_type(*instances, **{'repeat': repeat})

    def _parse_element(self, token):
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
        # --all=<sth>... -> --all=<sth> ...
        # --all=(<sth> <else>)... -> --all= ( <sth> <else> ) ...
        if atom.startswith('--') and '=' in atom:
            flag, arg = atom.split('=', 1)
            if Atom.get_class(flag) is Option:
                # --all=<sth>
                if arg and Atom.get_class(arg) is Argument:
                    if token and token.current() == '...':
                        repeat = True
                        token.next()
                    else:
                        repeat = False
                    return (Option(flag,
                                   ref=Required(Argument(arg),
                                                repeat=repeat)),)
                # --all= ( <sth> <else> ) ...
                else:
                    if token and token.current() in '([':
                        bracket = token.next()
                        flag_args = token.till_end_bracket(bracket)
                        flag_args.insert(0, bracket)
                        flag_args.append(')' if bracket == '(' else ']')
                        if token.current() == '...':
                            flag_args.append(token.next())
                        flag_arg_ins = self._parse_bracket(Token(flag_args))
                        return (Option(flag, ref=flag_arg_ins),)
        # -a<sth>
        elif atom.startswith('-') and '<' in atom:
            flag, partly_arg = atom.split('<', 1)
            flag_class = Atom.get_class(flag)
            arg_class = Atom.get_class('<' + partly_arg)
            if flag_class is Option and arg_class is Argument:
                repeat = False
                if token.current() == '...':
                    token.next()
                    repeat = True
                return (Option(flag,
                               ref=Required(Argument('<' + partly_arg),
                                            repeat=repeat)),)

        atom_class = Atom.get_class(atom)
        if (atom_class is Option and
                not atom.startswith('--') and
                len(atom) > 2 and
                self.stdopt):
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

    def _parse_pipe(self, lis):
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
        opt_names = []
        long_opt_names = set()
        # check if same option announced twice in Options
        opt_2_ins = {}
        for each in opts:
            opt = each[0]
            names = opt.get_option_name()
            for name in names:
                if name in opt_2_ins:
                    logger.critical('name: %s, opt_2_ins: %s', name, opt_2_ins)
                    raise DocpieError('%s announced more than once '
                                      'in Options' % name)
                opt_2_ins[name] = opt
            long_opt_names.update(filter(lambda x: x.startswith('--'), names))
            opt_names.append(names)
        # set the option shortcut
        # OptionsShortcut.set_ref(opts)

        usage_result = []

        logger.debug('origial usage: %s', usages)
        for usage in usages:
            if usage is None:
                usage_result.append(Optional())
            else:
                usage.fix_optional(opt_2_ins)
                opts_in_usage, shortcuts = \
                    cls.find_option_names_no_shortcut_and_shortcut(usage)
                if opts_in_usage and shortcuts:
                    for cut in shortcuts:
                        cut.set_hide(opts_in_usage)
                long_opt_names.update(
                    filter(lambda x: x.startswith('--'), opts_in_usage))
                usage_result.extend(usage.expand_either())

        for each in usage_result:
            each.push_option_ahead()

        logger.debug('fixed usage: %s', usage_result)

        return usage_result, opt_names, long_opt_names

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
            return None, None
        dic = match.groupdict()
        logger.debug(dic)
        if dic['sep'] == '\n':
            return dic['section'], dic['raw']
        reallen = len(dic['name'])
        replace = ''.ljust(reallen)
        drop_name = match.expand('%s\g<sep>\g<section>' % replace)
        return cls.drop_started_empty_lines(drop_name).rstrip(), dic['raw']

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

    def __init__(self, text, stdopt):
        self.stdopt = stdopt
        if text is None or not text.strip():    # empty
            self._opt_and_default_str = []
        else:
            self._opt_and_default_str = list(self._parse_text(text))

        self._chain = self._parse_to_instance(self._opt_and_default_str)

    def get_chain(self):
        return self._chain
        # return [Optional(x) for x in self._chain]

    def _parse_text(self, text):
        collect = []
        to_list = text.splitlines()

        # parse first line. Should NEVER failed.
        # this will ensure in `[default: xxx]`,
        # the `xxx`(e.g: `\t`, `,`) will not be changed by _format_line
        previous_line = to_list.pop(0)
        collect.append(self._parse_line(previous_line))

        for line in to_list:
            indent_match = self.indent_re.match(line)
            this_indent = len(indent_match.groupdict()['indent'])

            if this_indent >= collect[-1]['indent']:
                # A multi line description
                previous_line = line
                continue

            # new option line
            # deal the default for previous option
            collect[-1]['default'] = self._parse_default(previous_line)
            # deal this option
            collect.append(self._parse_line(line))
            logger.debug(collect[-1])
            previous_line = line
        else:
            collect[-1]['default'] = self._parse_default(previous_line)

        return ((each['option'], each['default']) for each in collect)

    spaces_re = re.compile(r'(\ \ \s*|\t\s*)')

    @classmethod
    def _cut_first_spaces_outside_bracket(cls, string):
        right = cls.spaces_re.split(string)
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
    def _parse_line(cls, line):
        opt_str, separater, description_str = \
                cls._cut_first_spaces_outside_bracket(line)

        logger.debug('%(line)s -> %(opt_str)r, '
                     '%(separater)r, '
                     '%(description_str)r' % locals())
        if description_str.strip():
            indent = len(opt_str.expandtabs()) + len(separater.expandtabs())
        else:
            indent = 2 + len(cls.indent_re.match(
                                 opt_str.expandtabs()
                            ).groupdict()['indent'])
        return {'option': opt_str.strip(), 'indent': indent}

    @classmethod
    def _parse_default(cls, line):
        m = cls.default_re.search(line)
        if m is None:
            return None
        return m.groupdict()['default']

    def _parse_to_instance(self, lis):
        opts = []
        for opt_str, default in lis:
            logger.debug('%s:%r' % (opt_str, default))
            opt, repeat = self._parse_opt_str(opt_str)
            opt.set_default(default)
            opts.append(Optional(opt, repeat=repeat))
        return opts

    def _split_short_by_cfg(self, s):
        if self.stdopt:
            if (not s.startswith('--') and
                    len(s) > 1):
                return s[:2], s[2:]
        return (s, '')

    def _parse_opt_str(self, opt):

        repeat = False

        # -sth=<goes> ON -> -sth, <goes>, ON
        opt_lis = self._opt_str_to_list(opt)
        logger.debug('%r -> %s' % (opt, opt_lis))

        first = opt_lis.pop(0)
        if not first.startswith('-'):
            raise DocpieError('option %s does not start with "-"' % first)

        # if Atom.stdopt:
        # -sth -> name=-s, value=th
        # else:
        # -sth -> name=-sth, value=''
        name, value = self._split_short_by_cfg(first)
        opt_ins = Option(name)
        if value == '...':
            repeat = True
            # -f... <sth>
            if opt_lis and not opt_lis[0].startswith('-'):
                raise DocpieError(
                    'option "%s" has argument following "..."', opt)
        elif value:
            args_ins = [Required(Argument(value))]
        else:
            args_ins = []

        if opt_lis and opt_lis[0] == '...':
            repeat = True
            opt_lis.pop(0)
            if opt_lis and not opt_lis[0].startswith('-'):
                raise DocpieError(
                    'option "%s" has argument following "..."', opt)

        args = []    # store the current args after option
        for each in opt_lis:
            if each.startswith('-'):    # alias
                name, value = self._split_short_by_cfg(each)
                opt_ins.set_alias(name)
                if value:
                    args_ins.append(Required(Argument(value)))
                if args:    # trun it into instance
                    if args[0] == '...':
                        if len(args) != 1:
                            raise DocpieError(
                                'Error in %s: "..." followed by non option',
                                opt)
                        repeat = True
                    else:
                        this_arg = Required(
                                            *self._parse_pattern(Token(args))
                                           ).fix()
                        if this_arg is not None:
                            args_ins.append(this_arg)
                del args[:]
            else:
                args.append(each)
        else:
            if args:    # trun it into instance
                if args[0] == '...':
                    if len(args) != 1:
                        raise DocpieError(
                            'Error in %s: "..." followed by non option',
                            opt)
                    repeat = True
                else:
                    this_arg = Required(
                        *self._parse_pattern(Token(args))).fix()
                    if this_arg is not None:
                        args_ins.append(this_arg)

        # option without any args
        if not args_ins:
            return opt_ins, repeat

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
            logger.info('too many possibilities: '
                           'option %s expect %s arguments',
                           name, '/'.join(map(str, current_range)))

        # TODO: check if current_ins contain Command(not allowed in fact)
        opt_ins.ref = current_ins
        return opt_ins, repeat

    def _opt_str_to_list(self, opt):
        dropped_comma_and_equal = opt.replace(',', ' ').replace('=', ' ')
        wrapped_space = self.wrap_symbol_re.sub(
            r' \1 ', dropped_comma_and_equal)
        opt_lis = [x for x in self.split_re.split(wrapped_space) if x]
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

    def __init__(self, text, name, stdopt):
        self.stdopt = stdopt
        self._chain = self._parse_text(text, name)

    def _parse_text(self, text, name):
        result = []
        for each_line in self._split_line_by_indent(text):
            raw_str_lis = self._parse_line_to_lis(each_line, name)
            chain = self._parse_pattern(Token(raw_str_lis))
            result.append(chain)
        return result

    indent_re = re.compile(r'^ *')

    def _split_line_by_indent(self, text):
        lines = text.splitlines()
        if len(lines) == 1:
            yield lines[0]
            return

        first_line = lines.pop(0)
        line_to_join = [first_line]
        indent = len(
            self.indent_re.match(first_line.expandtabs()).group())
        while lines:
            this_line = lines.pop(0)
            this_indent = len(
                self.indent_re.match(this_line.expandtabs()).group())

            if this_indent > indent:
                line_to_join.append(this_line)
            else:
                yield ''.join(line_to_join)
                line_to_join[:] = (this_line,)
                indent = len(
                    self.indent_re.match(this_line.expandtabs()).group())

        else:
            yield ' '.join(line_to_join)

    def _parse_line_to_lis(self, line, name=None):
        if name is not None:
            if name not in line:
                raise DocpieError(
                    '%s is not in usage pattern %s' % (name, line))

            _, line = line.split(name, 1)
        wrapped_space = self.wrap_symbol_re.sub(r' \1 ', line.strip())
        logger.debug(wrapped_space)
        result = [x for x in self.split_re.split(wrapped_space) if x]

        # drop name
        if name is None:
            result.pop(0)

        return result

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
