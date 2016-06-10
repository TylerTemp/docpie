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

    def parse_pattern(self, token):
        logger.debug('get token %s', token)
        elements = []
        while token:
            atom = token.current()
            if atom in '([':
                elements.append(self.parse_bracket(token))
            elif atom == '|':
                elements.append(token.next())
            else:
                assert atom != '...', 'fix me: unexpected "..." when parsing'
                elements.extend(self.parse_element(token))

        logger.debug(elements)
        if '|' in elements:
            elements[:] = [self.parse_pipe(elements)]
        logger.debug('parsed result %s', elements)
        return elements

    def parse_bracket(self, token):
        start = token.next()
        instance_type = Required if start == '(' else Optional

        lis = token.till_end_bracket(start)

        repeat = token.check_ellipsis_and_drop()

        bracket_token = Token(lis)

        instances = self.parse_pattern(bracket_token)

        return instance_type(*instances, **{'repeat': repeat})

    def parse_element(self, token):
        atom = token.next()
        assert atom is not None

        if atom in ('-', '--'):
            return self.parse_dash(atom , token)

        if atom.startswith('-'):
            result = self.parse_option_with_arg(atom, token)
            if result is not None:
                return result

        return self.parse_other_element(atom, token)

    def parse_option_with_arg(self, current, token):
        flag = None
        arg_token = None
        prepended = False

        # --all=<sth>... -> --all=<sth> ...
        # --all=(<sth> <else>)... -> --all= ( <sth> <else> ) ...
        if current.startswith('--') and '=' in current:
            flag, arg_token = self.get_long_option_with_arg(current, token)

        # -a<sth> -aSTH -asth, -a, -abc<sth>
        elif current.startswith('-') and not current.startswith('--'):
            flag, arg_token, prepended = \
                self.get_short_option_with_arg(current, token)

        if flag is not None:
            logger.debug('parsing flag %s, %s, %s', flag, arg_token, token)
            if arg_token is not None:
                ref_lis = self.parse_pattern(arg_token)
                ref = Required(*ref_lis).fix()
            else:
                ref = None
            ins = Option(flag, ref=ref)

            for opt_2_ins in self.titled_opt_to_ins.values():
                if flag in opt_2_ins:
                    opt_ins = opt_2_ins[flag][0]
                    ins.names.update(opt_ins.names)
                    # != won't work on pypy
                    if not (ins == opt_ins):
                        raise DocpieError(
                            '%s announces differently in '
                            'Options(%r) and Usage(%r)' %
                            (flag, opt_ins, ins))
                    break

            if token.current() == '...':
                ins = Required(ins, repeat=True)
                token.next()

            return (ins,)

        if prepended:
            token.pop(0)

    def get_long_option_with_arg(self, current, token):
        flag, arg = current.split('=', 1)
        if Atom.get_class(flag)[0] is Option:
            if arg:
                arg_token = Token([arg])
            else:
                next_arg = token.next()
                if next_arg not in '([':
                    raise DocpieError('format error: %s' % current)
                tk = [next_arg]
                tk.extend(token.till_end_bracket(next_arg))
                tk.append(')' if next_arg == '(' else ']')
                arg_token = Token(tk)

            if token.current() == '...':
                arg_token.append(token.next())

            return flag, arg_token

    def get_short_option_with_arg(self, current, token):
        flag = None
        arg_token = None
        rest = None
        prepended = False

        # -a<sth> -abc<sth>
        if current.find('<') >= 0 and current.endswith('>'):
            temp_flag, arg_token, prepended = \
                self.get_short_option_with_angle_bracket(current, token)
        else:
            temp_flag, rest = current[:2], current[2:]

        if Atom.get_class(temp_flag)[0] is Option:
            flag = temp_flag
            arg_token, prepended = \
                self.get_short_option_arg(flag, token, arg_token, rest)

        return flag, arg_token, prepended

    def get_short_option_with_angle_bracket(self, current, token):
        lt_index = current.find('<')
        prepended = False
        arg_token = None
        if self.stdopt and self.attachopt:
            # -a<sth> -> -a <sth>; -abc<sth> -> -a -bc<sth>
            if not self.attachvalue:
                raise DocpieError(
                    "You can't write %s while attachvalue=False" %
                    current)

            flag = current[:2]
            # -abc<sth>
            if lt_index > 2:
                token.insert(0, '-' + current[2:])
                prepended = True
            # -a<sth>
            else:
                arg_token = Token([current[lt_index:]])
                # rest = atom[lt_index:]
        # -a<sth> -> -a <sth>; -abc<sth> -> -abc <sth>
        else:
            flag = current[:lt_index]
            arg_token = Token([current[lt_index:]])

        return flag, arg_token, prepended

    def get_short_option_arg(self, current, token, arg_token, rest):
        prepended = False

        opt_2_ins = {}
        # TODO: Better solution, maybe cache one
        for options in self.titled_opt_to_ins.values():
            opt_2_ins.update(options)

        if current in opt_2_ins:
            ins = opt_2_ins[current][0]
            # In Options it requires no argument
            if ins.ref is None:
                # sth stacked with it
                if rest:
                    if Atom.get_class(rest)[0] is Argument:
                        raise DocpieError(
                            ('%s announced difference in '
                             'Options(%s) and Usage(%s)') %
                            (current, ins, current))
                    if not (self.stdopt and self.attachopt):
                        raise DocpieError(
                            ("You can't write %s while it requires "
                             "argument and attachopt=False") % current)

                    token.insert(0, '-' + rest)
                    prepended = True
            # In Options it requires argument
            else:
                if rest:
                    arg_token = Token([rest])
                elif arg_token:
                    pass
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
                            current, ins, _current)
                    else:
                        arg_token = Token([token.next()])

                if token.current() == '...':
                    arg_token.append(token.next())
        elif rest:
            if not (self.stdopt and self.attachopt):
                raise DocpieError(
                    "You can't write %s while it requires argument "
                    "and attachopt=False" % current)
            # -asth -> -a -sth
            token.insert(0, '-' + rest)
            prepended = True

        return arg_token, prepended

    def parse_other_element(self, current, token):
        atom_class, title = Atom.get_class(current)
        if atom_class is OptionsShortcut:
            return self.parse_options_shortcut(title, token)

        args = set([current])

        if atom_class is Option:
            for options in self.titled_opt_to_ins.values():
                if current in options:
                    ins_in_opt = options[current][0]

                    args.update(ins_in_opt.names)
                    if ins_in_opt.ref is not None:
                        ref_current = token.next()
                        ref_token = Token()
                        if ref_current in '([':
                            ref_token.append(ref_current)
                            ref_token.extend(token.till_end_bracket(ref_current))
                            ref_token.append(')' if ref_current == '(' else ']')
                        else:
                            ref_token.extend(('(', ref_current, ')'))

                        ref_ins = self.parse_pattern(ref_token)

                        logger.debug(ins_in_opt.ref)
                        logger.debug(ref_ins[0])

                        if len(ref_ins) != 1:
                            raise DocpieError(
                                '%s announced difference in Options(%s) and Usage(%s)' %
                                (current, ins_in_opt, ref_ins))

                        if ins_in_opt.ref != ref_ins[0]:
                            raise DocpieError(
                                '%s announced difference in Options(%s) and Usage(%s)' %
                                (current, ins_in_opt, ref_ins))

                        ins = atom_class(*args, **{'ref': ins_in_opt.ref})
                        return (ins,)

        ins = atom_class(*args)

        repeat = token.check_ellipsis_and_drop()
        if repeat:
            ins = Required(ins, repeat=True)
        logger.debug('%s -> %s', current, ins)
        return (ins,)

    def parse_options_shortcut(self, title, token):
        # `[options] ...`? Note `[options...]` won't work
        options = self.find_options(title, self.options)
        ins = OptionsShortcut(title, options)
        repeat = token.check_ellipsis_and_drop()
        if repeat:
            ins = Optional(ins, repeat=True)

        return (ins,)

    def find_options(self, title, title_opt_2_ins):
        formal_title = self.formal_title(title)
        if self.namedoptions:
            for exists_title, options in title_opt_2_ins.items():
                if (formal_title == self.formal_title(exists_title)):
                    logger.debug('find %s for %s', exists_title, title)
                    return options
            else:
                logger.debug('%s options not found in %s',
                            title, title_opt_2_ins)
                raise DocpieError('%s options not found' % title)

        return sum(title_opt_2_ins.values(), [])

    formal_title_re = re.compile('[\-_]')

    def formal_title(self, title):
        return self.formal_title_re.sub(' ', title.lower()).strip()

    def parse_dash(self, current, token):
        repeat = token.check_ellipsis_and_drop()
        return (Command(current, repeat=repeat),)

    def parse_pipe(self, lis):
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

    started_empty_lines = re.compile(r'^\s*?\n(?P<rest>.*)')

    @classmethod
    def drop_started_empty_lines(cls, text):
        # drop the empty lines at start
        # different from lstrip
        logger.debug(repr(text))
        m = cls.started_empty_lines.match(text)
        if m is None:
            return text
        return m.groupdict()['rest']


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

    visible_empty_line_re = re.compile(r'^\s*?\n*|\r?\n(:?[\ \t]*\r?\n)+',
                                       flags=re.DOTALL)

    option_split_re_str = (r'([^\r\n]*{0}[\ \t]*\r?\n?)')

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

    def __init__(self, option_name, case_sensitive,
                 stdopt, attachopt, attachvalue, namedoptions):

        self.stdopt = stdopt
        self.attachopt = attachopt
        self.attachvalue = attachvalue
        self.case_sensitive = case_sensitive
        self.option_name = option_name
        self.option_split_re = re.compile(
            self.option_split_re_str.format(option_name),
            flags= re.DOTALL if case_sensitive else (re.DOTALL | re.IGNORECASE)
        )

        self.raw_content = {}
        self.formal_content = None
        self.name_2_instance = {}
        self.namedoptions = namedoptions

        # if text is None or not text.strip():    # empty
        #     self._opt_and_default_str = []
        # else:
        #     self._opt_and_default_str = list(self._parse_text(text))
        #
        # self._chain = self._parse_to_instance(self._opt_and_default_str)

    def parse(self, text):
        self.parse_content(text)
        title_names_and_default = self.parse_names_and_default()
        self.instances = self.parse_to_instance(title_names_and_default)

    def parse_content(self, text):
        """parse section to formal format

        raw_content: {title: section(with title)}. For `help` access.

        formal_content: {title: section} but the section has been dedented
        without title. For parse instance"""
        raw_content = self.raw_content
        raw_content.clear()
        formal_collect = {}

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                split = self.visible_empty_line_re.split(text)
            except ValueError:  # python >= 3.5
                split = [text]

        option_split_re = self.option_split_re
        name = re.compile(re.escape(self.option_name), re.IGNORECASE)
        for text in filter(lambda x: x and x.strip(), split):

            # logger.warning('get options group:\n%r', text)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    split_options = option_split_re.split(text)
                except ValueError:  # python >= 3.5
                    continue

            split_options.pop(0)

            for title, section in zip(split_options[::2], split_options[1::2]):
                prefix, end = name.split(title)

                prefix = prefix.strip()

                section = section.rstrip()
                if end.endswith('\n'):
                    formal = section
                else:
                    formal = ' ' * len(title) + section

                formal_collect.setdefault(prefix, []).append(formal)

                # logger.error((title, section))
                if prefix in raw_content:
                    # TODO: better handling way?
                    if self.namedoptions:
                        log = logger.warning
                    else:
                        log = logger.debug
                    log('duplicated options section %s', prefix)

                    raw_content[prefix] += '\n%s%s' % (title, section)
                else:
                    raw_content[prefix] = title + section

        if formal_collect:
            for each_title, values in formal_collect.items():
                value = '\n'.join(map(textwrap.dedent, values))
                formal_collect[each_title] = value

        self.formal_content = formal_collect

    def parse_names_and_default(self):
        """parse for `parse_content`
        {title: [('-a, --all=STH', 'default'), ...]}"""
        result = {}
        for title, text in self.formal_content.items():

            if not text:
                result[title] = []
                continue

            logger.debug('\n' + text)

            collect = []
            to_list = text.splitlines()

            # parse first line. Should NEVER failed.
            # this will ensure in `[default: xxx]`,
            # the `xxx`(e.g: `\t`, `,`) will not be changed by _format_line
            previous_line = to_list.pop(0)
            collect.append(self.parse_line_option_indent(previous_line))

            for line in to_list:
                indent_match = self.indent_re.match(line)
                this_indent = len(indent_match.groupdict()['indent'])

                if this_indent >= collect[-1]['indent']:
                    # A multi line description
                    previous_line = line
                    continue

                # new option line
                # deal the default for previous option
                collect[-1]['default'] = self.parse_default(previous_line)
                # deal this option
                collect.append(self.parse_line_option_indent(line))
                logger.debug(collect[-1])
                previous_line = line
            else:
                collect[-1]['default'] = self.parse_default(previous_line)

            result[title] = [
                (each['option'], each['default']) for each in collect]

        return result

    spaces_re = re.compile(r'(\ \ \s*|\t\s*)')

    @classmethod
    def cut_first_spaces_outside_bracket(cls, string):
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
    def parse_line_option_indent(cls, line):
        opt_str, separater, description_str = \
                cls.cut_first_spaces_outside_bracket(line)

        logger.debug('%(line)s -> %(opt_str)r, '
                     '%(separater)r, '
                     '%(description_str)r' % locals())
        if description_str.strip():
            indent = len(opt_str.expandtabs()) + len(separater.expandtabs())
            logger.debug('indent: %s', indent)
        else:
            indent = 2 + len(cls.indent_re.match(
                                 opt_str.expandtabs()
                            ).groupdict()['indent'])
            logger.debug('indent: %s', indent)
        return {'option': opt_str.strip(), 'indent': indent}

    @classmethod
    def parse_default(cls, line):
        m = cls.default_re.search(line)
        if m is None:
            return None
        return m.groupdict()['default']

    def parse_to_instance(self, title_of_name_and_default):
        """{title: [Option(), ...]}"""
        result = {}
        for title, name_and_default in title_of_name_and_default.items():
            logger.debug((title, name_and_default))
            result[title] = opts = []
            for opt_str, default in name_and_default:
                logger.debug('%s:%r' % (opt_str, default))
                opt, repeat = self.parse_opt_str(opt_str)
                opt.default = default
                opt_ins = Optional(opt, repeat=repeat)
                for name in opt.names:
                    self.name_2_instance[name] = opt_ins
                opts.append(opt_ins)

        return result

    def split_short_by_cfg(self, option_str):
        if self.stdopt:
            if (not option_str.startswith('--') and
                    len(option_str) > 1):
                return option_str[:2], option_str[2:]
        return option_str, ''

    def parse_opt_str(self, opt):

        repeat = False

        # -sth=<goes> ON -> -sth, <goes>, ON
        opt_lis = self.opt_str_to_list(opt)
        logger.debug('%r -> %s' % (opt, opt_lis))

        first = opt_lis.pop(0)
        if not first.startswith('-'):
            raise DocpieError('option %s does not start with "-"' % first)

        # if self.stdopt:
        # -sth -> name=-s, value=th
        # else:
        # -sth -> name=-sth, value=''
        name, value = self.split_short_by_cfg(first)
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
                name, value = self.split_short_by_cfg(each)
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
                                            *self.parse_pattern(Token(args))
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
                        *self.parse_pattern(Token(args))).fix()
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
            logger.debug('too many possibilities: '
                        'option %s expect %s arguments',
                        name, '/'.join(map(str, current_range)))

        # TODO: check if current_ins contain Command(not allowed in fact)
        opt_ins.ref = current_ins
        return opt_ins, repeat

    def opt_str_to_list(self, opt):
        dropped_comma_and_equal = opt.replace(',', ' ').replace('=', ' ')
        wrapped_space = self.wrap_symbol_re.sub(
            r' \1 ', dropped_comma_and_equal)
        opt_lis = [x for x in self.split_re.split(wrapped_space) if x]
        return opt_lis


class UsageParser(Parser):

    angle_bracket_re = re.compile(r'(<.*?>)')
    wrap_symbol_re = re.compile(r'(\[[^\]\s]*?options\]|\.\.\.|\||\[|\]|\(|\))')
    split_re = re.compile(r'(\[[^\]\s]*?options\]|\S*<.*?>\S*)|\s+')
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
                     r'(?P<sep>(\r?\n)?)'
                     r'(?P<section>.*?)'
                    r')'
                    r'\s*'
                    r'(?:\n\s*\n|\n\s*$|$)')

    def __init__(self, usage_name, case_sensitive,
                 stdopt, attachopt, attachvalue, namedoptions):

        self.usage_name = re.escape(usage_name)
        self.case_sensitive = case_sensitive
        self.stdopt = stdopt
        self.attachopt = attachopt
        self.attachvalue = attachvalue

        self.titled_opt_to_ins = {}
        self.options = None
        self.raw_content = None
        self.formal_content = None
        self.instances = None
        self.all_options = None
        self.namedoptions = namedoptions
        # self._chain = self._parse_text(text, name)

    def parse(self, text, name, options):
        self.options = options
        self.set_option_name_2_instance(options)
        if text is not None:
            self.parse_content(text)
        if self.formal_content is None:
            raise DocpieError('"Usage:" not found')
        self.parse_2_instance(name)
        self.fix_option_and_empty()

    def set_option_name_2_instance(self, options):
        """{title: {'-a': Option(), '--all': Option()}}"""
        title_opt_2_ins = self.titled_opt_to_ins
        title_opt_2_ins.clear()
        for title, opts in options.items():
            title_opt_2_ins[title] = opt_2_ins = {}
            for each in opts:
                opt_ins = each[0]  # get Option inside Optional/Required
                for name in opt_ins.names:
                    opt_2_ins[name] = each

    def parse_content(self, text):
        """get Usage section and set to `raw_content`, `formal_content` of no
        title and empty-line version"""
        match = re.search(
            self.usage_re_str.format(self.usage_name),
            text,
            flags=(re.DOTALL
                   if self.case_sensitive
                   else (re.DOTALL | re.IGNORECASE)))

        if match is None:
            return

        dic = match.groupdict()
        logger.debug(dic)
        self.raw_content = dic['raw']
        if dic['sep'] in ('\n', '\r\n'):
            self.formal_content = dic['section']
            return

        reallen = len(dic['name'])
        replace = ''.ljust(reallen)
        drop_name = match.expand('%s\g<sep>\g<section>' % replace)
        self.formal_content = self.drop_started_empty_lines(drop_name).rstrip()

    def parse_2_instance(self, name):
        result = []
        for each_line in self.split_line_by_indent(self.formal_content):
            raw_str_lis = self.parse_line_to_lis(each_line, name)
            chain = self.parse_pattern(Token(raw_str_lis))
            result.append(chain)
        self.instances = result

    indent_re = re.compile(r'^ *')

    def split_line_by_indent(self, text):
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

    def parse_line_to_lis(self, line, name=None):
        if name is not None:
            _, find_name, line = line.partition(name)
            if not find_name:
                raise DocpieError(
                    '%s is not in usage pattern %s' % (name, _))

        # wrapped_space = self.wrap_symbol_re.sub(r' \1 ', line.strip())
        # logger.debug(wrapped_space)
        # result = [x for x in self.split_re.split(wrapped_space) if x]

        angle_bracket_re = self.angle_bracket_re
        wrap_symbol_re = self.wrap_symbol_re

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                sep_by_angle = angle_bracket_re.split(line)
            except ValueError:
                sep_by_angle = [line]

        wrap_space = []
        for index, each_block in enumerate(sep_by_angle):
            if index % 2:
                wrap_space.append(each_block)
                continue

            if not each_block:
                continue

            warped_space = wrap_symbol_re.sub(r' \1 ', each_block)

            wrap_space.append(warped_space)

        wraped = ''.join(wrap_space)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                sep = self.split_re.split(wraped)
            except ValueError:
                sep = [wraped]

        result = list(filter(None, sep))

        # drop name
        if name is None:
            result.pop(0)

        return result

    @classmethod
    def find_optionshortcut_and_outside_option_names(cls, lis):
        opt_ouside = []
        opt_cuts = []
        for element in lis:
            if isinstance(element, OptionsShortcut):
                opt_cuts.append(element)
            elif isinstance(element, list):
                outside, srtcuts = \
                    cls.find_optionshortcut_and_outside_option_names(element)
                opt_ouside.extend(outside)
                opt_cuts.extend(srtcuts)
            elif isinstance(element, Option):
                opt_ouside.append(element)

        return opt_ouside, opt_cuts

    def fix_option_and_empty(self):
        result = []
        all_options = []
        logger.debug(self.titled_opt_to_ins)
        for options in self.titled_opt_to_ins.values():
            for each_potion in options.values():
                all_options.append(each_potion[0])

        for each_usage in self.instances:
            ins = Required(*each_usage).fix()
            if ins is None:
                result.append(Optional())
                continue

            outside_opts, opt_shortcuts = \
                self.find_optionshortcut_and_outside_option_names(ins)


            logger.debug(outside_opts)

            for opt_cut in opt_shortcuts:
                for opt_ins in outside_opts:
                    opt_cut.set_hide(opt_ins.names)

            all_options.extend(outside_opts)

            for usage in ins.expand():
                usage.push_option_ahead()
                # [options] -a
                # Options: -a
                # TODO: better solution
                r = usage.fix()
                if r is None:
                    result.append(Optional())
                else:
                    result.append(r)

        self.instances = result
        self.all_options = all_options
