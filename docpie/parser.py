from docpie.element import Atom, Option, Command, Argument
from docpie.element import Optional, Required, OptionsShortcut
from docpie.element import Either
from docpie.tokens import Token
from docpie.error import DocpieError

import logging
import re
import textwrap
import warnings

logger = logging.getLogger('docpie.parser')


class Parser(object):

    option_name_2_instance = {}

    def _parse_pattern(self, token):
        logger.debug('get token %s', token)
        elements = []
        while token:
            atom = token.current()
            if atom in '([':
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
        start = token.next()
        instance_type = Required if start == '(' else Optional

        lis = token.till_end_bracket(start)

        repeat = False
        while token.current() == '...':
            repeat = True
            token.next()

        bracket_token = Token(lis)

        instances = self._parse_pattern(bracket_token)

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
                ins = Optional(OptionsShortcut(self.options), repeat=True)
            else:
                ins = OptionsShortcut(self.options)
            return (ins,)

        if atom in ('-', '--'):
            if token.current() == '...':
                repeat = True
                token.next()
            else:
                repeat = False
            return (Command(atom, repeat=repeat),)

        flag = None
        arg_token = None
        prepended = False
        opt_2_ins = self.option_name_2_instance

        # --all=<sth>... -> --all=<sth> ...
        # --all=(<sth> <else>)... -> --all= ( <sth> <else> ) ...
        if atom.startswith('--') and '=' in atom:
            flag_, arg_ = atom.split('=', 1)
            if Atom.get_class(flag_) is Option:
                flag = flag_
                if arg_:
                    arg_token = Token([arg_])
                else:
                    next_arg = token.next()
                    if next_arg not in ('(', '['):
                        raise DocpieError('format error: %s' % atom)
                    tk = [next_arg]
                    tk.extend(token.till_end_bracket(next_arg))
                    tk.append(')' if next_arg == '(' else ']')
                    arg_token = Token(tk)

                if token.current() == '...':
                    arg_token.append(token.next())

            # if '<' in atom and atom.endswith('>'):
            #  and not self.stdopt:
            #     index = atom.index('<')
            #     flag_, arg_ = atom[:index], atom[index:]
            #     if Atom.get_class(flag_) is Option:
            # and Atom.get_class(arg_) is Argument:
            #         flag = flag_
            #         arg_token = Token([arg_])

        # -a<sth> -aSTH -asth, -a, -abc<sth>
        elif atom.startswith('-') and not atom.startswith('--'):
            rest = None

            lt_index = atom.find('<')
            # -a<sth> -abc<sth>
            if lt_index >= 0 and atom.endswith('>'):
                # -a<sth> -> -a <sth>; -abc<sth> -> -a -bc<sth>
                if self.stdopt and self.attachopt:
                    if not self.attachvalue:
                        raise DocpieError(
                            "You can't write %s while attachvalue=False" %
                            atom)
                    flag_ = atom[:2]
                    # -abc<sth>
                    if lt_index > 2:
                        token.insert(0, '-' + atom[2:])
                        prepended = True
                    else:
                        arg_token = Token([atom[lt_index:]])
                # -a<sth> -> -a <sth>; -abc<sth> -> -abc <sth>
                else:
                    flag_ = atom[:lt_index]
                    arg_token = Token([atom[lt_index:]])
            else:
                flag_, rest = atom[:2], atom[2:]

            if Atom.get_class(flag_) is Option:
                flag = flag_
                # announced in Options
                if flag in opt_2_ins:
                    ins = opt_2_ins[flag_][0]
                    # In Options it requires no argument
                    if ins.ref is None:
                        # sth stacked with it
                        if rest:
                            if Atom.get_class(rest) is Argument:
                                raise DocpieError(
                                    ('%s announced difference in '
                                     'Options(%s) and Usage(%s)') %
                                    (flag_, ins, atom))
                            if not (self.stdopt and self.attachopt):
                                raise DocpieError(
                                    ("You can't write %s while it requires "
                                     "argument and attachopt=False") % atom)

                            token.insert(0, '-' + rest)
                            prepended = True
                    # In Options it requires argument
                    else:
                        if rest:
                            arg_token = Token([rest])
                        else:
                            _current = token.current()
                            if _current in '([':
                                tk = [token.next()]
                                tk.extend(token.till_end_bracket(tk[0]))
                                tk.append(')' if tk[0] == '(' else ']')
                                arg_token = Token(tk)
                            elif _current in ('...', '|'):
                                raise DocpieError(
                                    ('%s requires argument in Options(%s) '
                                     'but hit "%s" in Usage') %
                                    atom, ins, _current)
                            else:
                                arg_token = Token([token.next()])

                        if token.current() == '...':
                            arg_token.append(token.next())
                elif rest:
                    if not (self.stdopt and self.attachopt):
                        raise DocpieError(
                            "You can't write %s while it requires argument "
                            "and attachopt=False" % atom)
                    # -asth -> -a -sth
                    token.insert(0, '-' + rest)
                    prepended = True

        if flag is not None:
            logger.debug('parsing flag %s, %s, %s', flag, arg_token, token)
            if arg_token is not None:
                ref_lis = self._parse_pattern(Token(arg_token))
                ref = Required(*ref_lis).fix()
            else:
                ref = None
            ins = Option(flag, ref=ref)

            if flag in opt_2_ins:
                opt_ins = opt_2_ins[flag][0]
                ins.names.update(opt_ins.names)
                # != won't work on pypy
                if not (ins == opt_ins):
                    raise DocpieError(
                        '%s announces differently in '
                        'Options(%r) and Usage(%r)' %
                        (atom, opt_ins, ins))
            if token.current() == '...':
                ins = Required(ins, **{'repeat': True})
                token.next()

            return (ins,)

        if prepended:
            token.pop(0)

        atom_class = Atom.get_class(atom)
        ins = atom_class(atom)

        if token.current() == '...':
            token.next()
            # Not work on py2.6
            # ins = Required(*ins_lis, repeat=True)
            ins = Required(ins, **{'repeat': True})

        return (ins,)

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

    @staticmethod
    def drop_started_empty_lines(text):
        # drop the empty lines at start
        # different from lstrip
        logger.debug(repr(text))
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

    visible_empty_line_re = re.compile(r'^\s*?\n*|\n(:?[\ \t]*\n)+',
                                       flags=re.DOTALL)

    option_split_re_str = (r'([^\n]*{0}[\ \t]*\n?)')

    # split_re = re.compile(r'(<.*?>)|\s?')
    # default ::= chars "[default: " chars "]"
    # support xxxxxx.[default: ]
    # support xxxxxx.[default: yes]
    # not support xxxxx[default: no].
    # not support xxxxx[default: no]!
    # If you want to match a not so strict format, this may help:
    # default_re = re.compile(r'\[default: *(?P<default>.*?) *\]'
    #                         r' *'
    #                         r'[\.\?\!]? *$',
    #                         flags=re.IGNORECASE)
    default_re = re.compile(r'\[default: (?P<default>.*?)\] *$',
                            flags=re.IGNORECASE)

    def __init__(self, text, stdopt, attachopt, attachvalue):

        self.stdopt = stdopt
        self.attachopt = attachopt
        self.attachvalue = attachvalue

        self.name_2_instance = {}
        if text is None or not text.strip():    # empty
            self._opt_and_default_str = []
        else:
            self._opt_and_default_str = list(self._parse_text(text))

        self._chain = self._parse_to_instance(self._opt_and_default_str)

    def get_chain(self):
        return self._chain
        # return [Optional(x) for x in self._chain]

    @classmethod
    def parse(cls, text, name, case_sensitive=False):
        # TODO: allow options separate with single break line
        # currently:
        # different option section must be separated with at
        # least one visible empty line
        #
        # Options:
        #   -f, --flag     a flag
        #
        # Help Options:
        #   -o, --output   output stream

        es_name = re.escape(name)

        option_split_re = re.compile(
            cls.option_split_re_str.format(es_name),
            flags=re.DOTALL | (0 if case_sensitive else re.IGNORECASE)
        )

        raw_content = {}
        formal_collect = []

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                split = cls.visible_empty_line_re.split(text)
        except ValueError:  # python >= 3.5
            return None, {}

        for text in filter(lambda x: x and x.strip(), split):

            # logger.debug('get options group:\n%r', text)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    split_options = option_split_re.split(text)
            except ValueError:  # python >= 3.5
                continue

            split_options.pop(0)

            for title, section in zip(split_options[::2], split_options[1::2]):
                prefix, _, end = title.partition(name)

                prefix = prefix.strip()

                if prefix in raw_content:
                    raise DocpieError('duplicated options section %s' % prefix)

                section = section.rstrip()
                if end.endswith('\n'):
                    formal = section
                else:
                    formal = ' ' * len(title) + section

                formal_collect.append(formal)
                raw_content[prefix] = title + section

        if formal_collect:
            formal_result = '\n'.join(
                textwrap.dedent(x) for x in formal_collect)
        else:
            formal_result = None

        return formal_result, raw_content

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
            opt.default = default
            result = Optional(opt, repeat=repeat)
            for name in opt.names:
                self.name_2_instance[name] = result
            opts.append(result)
        return opts

    def _split_short_by_cfg(self, s):
        if self.stdopt:
            if (not s.startswith('--') and
                    len(s) > 1):
                return s[:2], s[2:]
        return s, ''

    def _parse_opt_str(self, opt):

        repeat = False

        # -sth=<goes> ON -> -sth, <goes>, ON
        opt_lis = self._opt_str_to_list(opt)
        logger.debug('%r -> %s' % (opt, opt_lis))

        first = opt_lis.pop(0)
        if not first.startswith('-'):
            raise DocpieError('option %s does not start with "-"' % first)

        # if self.stdopt:
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
                opt_ins.names.add(name)
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

    usage_re_str = (r'(?:^|\n)'
                    r'(?P<raw>'
                     r'(?P<name>[\ \t]*{0}[\ \t]*)'
                     r'(?P<sep>\n?)'
                     r'(?P<section>.*?)'
                    r')'
                    r'\s*'
                    r'(?:\n\s*\n|\n\s*$|$)')

    def __init__(self, text, name, options, option_name_2_instance,
                 stdopt, attachopt, attachvalue):

        self.option_name_2_instance = option_name_2_instance
        self.options = options

        self.stdopt = stdopt
        self.attachopt = attachopt
        self.attachvalue = attachvalue
        self._chain = self._parse_text(text, name)

    @classmethod
    def parse(cls, text, name, case_sensitive=False):
        name = re.escape(name)
        match = re.search(
            cls.usage_re_str.format(name),
            text,
            flags=re.DOTALL | (0 if case_sensitive else re.IGNORECASE))

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

    @classmethod
    def _find_optionshortcut_and_outside_option_names(cls, lis):
        opt_ouside = []
        opt_cuts = []
        for element in lis:
            if isinstance(element, OptionsShortcut):
                opt_cuts.append(element)
            elif isinstance(element, list):
                outside, srtcuts = \
                    cls._find_optionshortcut_and_outside_option_names(element)
                opt_ouside.extend(outside)
                opt_cuts.extend(srtcuts)
            elif isinstance(element, Option):
                opt_ouside.append(element)

        return opt_ouside, opt_cuts

    def get_chain_and_all_options(self):
        result = []
        all_options = [x[0] for x in self.option_name_2_instance.values()]
        for each_usage in self._chain:
            ins = Required(*each_usage).fix()
            if ins is None:
                result.append(Optional())
                continue

            outside_opts, opt_shortcuts = \
                self._find_optionshortcut_and_outside_option_names(ins)

            for opt_cut in opt_shortcuts:
                for opt_ins in outside_opts:
                    opt_cut.set_hide(opt_ins.names)

            all_options.extend(outside_opts)

            for usage in ins.expand_either():
                usage.push_option_ahead()
                result.append(usage)

        return result, all_options
