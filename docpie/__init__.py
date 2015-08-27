"""
an easy and Pythonic command-line interface parser.
 * https://github.com/TylerTemp/docpie
 * Repository and issue-tracker: https://github.com/TylerTemp/docpie
 * Licensed under terms of MIT license (see LICENSE)
 * Copyright (c) 2013 TylerTemp, tylertempdev@gmail.com
"""

import sys
import re
import logging

from docpie.error import DocpieException, DocpieExit, DocpieError
from docpie.parser import UsageParser, OptionParser, Parser
from docpie.element import Atom, OptionsShortcut, \
                           convert_2_object, convert_2_dict
from docpie.tokens import Argv
from docpie.saver import Saver

__all__ = ('docpie', 'Docpie', 'DocpieException', 'DocpieExit', 'DocpieError')

__version__ = '0.0.1'

try:
    StrType = basestring
except NameError:
    StrType = str

logger = logging.getLogger('docpie')


class Docpie(dict):

    option_name = 'Options:'
    usage_name = 'Usage:'
    case_sensitive = False
    auto2dashes = True
    name = None
    help = True
    version = None
    extra = {}
    opt_names = []

    def __init__(self, doc=None, help=True, version=None,
                 stdopt=True, attachopt=True, attachvalue=True,
                 auto2dashes=True, name=None, case_sensitive=False, extra={}):

        # set config first
        self.set_config(
            stdopt=stdopt, attachopt=attachopt, attachvalue=attachvalue,
            auto2dashes=auto2dashes, name=name, case_sensitive=case_sensitive,
            extra={})

        if doc is not None:
            self.doc = doc
            self.usage_text = Parser.parse_section(doc, self.usage_name,
                                                   self.case_sensitive)
            self.option_text = Parser.parse_section(doc, self.option_name,
                                                    self.case_sensitive)
            assert self.usage_text is not None
            DocpieException.usage_str = 'Usage:\n%s' % self.usage_text
            DocpieException.opt_str = 'Options:\n%s' % self.option_text

            _, self.usages = Parser.fix(
                OptionParser(self.option_text).get_chain(),
                UsageParser(self.usage_text, self.name).get_chain()
            )

            # don't operate on the class level list
            self.opt_names = opt_names = []
            for each in OptionsShortcut._ref:
                opt_names.append(each.get_option_name())
            logger.debug(self.opt_names)

            self.set_config(help=help, version=version)

    @property
    def stdopt(self):
        return Atom.stdopt

    @stdopt.setter
    def stdopt(self, value):
        Atom.stdopt = value

    @property
    def attachopt(self):
        return Atom.attachopt

    @attachopt.setter
    def attachopt(self, value):
        Atom.attachopt = value

    @property
    def attachvalue(self):
        return Atom.attachvalue

    @attachvalue.setter
    def attachvalue(self, value):
        Atom.attachvalue = value

    def need_pickle(self):
        '''Return all the obejct that needs serialization by pickle.

        You can use it like:

        pie = Docpie(__doc__)
        with open("save.pickle", "rb") as f:
            pickle.dump(f, pie.need_pickle())

        Then use Docpie.restore_pickle to restore.
        '''
        return self, OptionsShortcut._ref

    @staticmethod
    def restore_pickle(value):
        '''Fully restore Docpie, return Docpie instance

        You can use it like:

        pie = Docpie(__doc__)
        pickled = pickle.dumps(pie.need_pickle())
        cloned_pie = Docpie.restore_pickle(picked)
        '''
        self, OptionsShortcut._ref = value
        return self

    def docpie(self, argv=None):
        '''match the argv for each usages, return None.

        if argv is None, it will use sys.argv instead.
        if argv is str, it will call argv.split() first.
        this function will check the options in self.extra and handle it first.
        Which means it may not try to match any usages because of the checking.
        '''
        if argv is None:
            argv = sys.argv
        elif isinstance(argv, StrType):
            argv = argv.split()

        token = Argv(argv[1:], self.auto2dashes)

        self.check_flag_and_handler(token)
        token.check_dash()

        for each in self.usages:
            logger.debug('matching usage %s', each)
            argv_clone = token.clone()
            saver = Saver()
            if each.match(argv_clone, saver):
                logger.debug('matched usage %s, checking rest argv %s',
                             each, argv_clone)
                if (not argv_clone or
                        (argv_clone.auto_dashes and
                         list(argv_clone) == ['--'])):
                    logger.info('matched usage %s / %s', each, argv_clone)
                    matched = each
                    break
                logger.info('matching %s left %s, checking failed',
                            each, argv_clone)
                continue
            else:
                logger.info('failed matching usage %s / %s', each, argv_clone)
        else:
            logger.info('none matched')
            raise DocpieExit(DocpieException.usage_str)

        value = matched.get_value(False)
        logger.debug('get all matched value %s', value)
        rest = self.usages
        rest.remove(matched)
        options = OptionsShortcut._ref

        for each in rest:  # add left command/argv
            default_values = each.get_sys_default_value()
            logger.debug('get rest values %s', default_values)
            common_keys = set(value).intersection(default_values)

            for key in common_keys:
                default = default_values[key]
                valued = value[key]

                if default not in (True, False) and isinstance(default, int):
                    valued = int(valued)
                elif isinstance(default, list):
                    if valued is None:
                        valued = []
                    elif isinstance(valued, list):
                        pass
                    else:
                        valued = [valued]

                default_values[key] = valued

            value.update(default_values)

        logger.debug('merged rest values, now %s', value)

        # add left option, add default value
        for option in options:
            names = option._names
            default = option._default
            this_value = option.value

            logger.debug('%s/%s/%s', option, default, this_value)

            name_in_value = names.intersection(value)
            if name_in_value:  # add default if necessary
                one_name = name_in_value.pop()
                value_in_usage = value[one_name]
                if not value_in_usage:  # need default
                    if default is None:  # no default, use old matched one
                        final_value = value_in_usage
                    elif (value_in_usage not in (True, False) and
                            isinstance(value_in_usage, (int, list))):
                        final_value = default.split()
                    else:
                        final_value = default
                else:
                    final_value = value_in_usage
            # just add this key-value. Note all option here never been matched
            else:
                ref = option._ref

                if default is not None:
                    if (this_value not in (True, False) and
                            isinstance(this_value, (int, list))):
                        final_value = default.split()
                    else:
                        if ref is not None and max(ref.arg_range()) > 1:
                            final_value = default.split()
                        else:
                            final_value = default
                else:
                    if ref is not None:
                        arg_range = ref.arg_range()
                        if min(arg_range) != 0:
                            # It requires at least a value
                            logger.info('%s expects value', option)
                            raise DocpieExit(DocpieException.usage_str)
                        elif max(arg_range) == 1:
                            final_value = None
                        else:
                            assert max(arg_range) > 1
                            final_value = []
                    # ref is None
                    elif this_value is None:
                        final_value = False
                    else:
                        final_value = this_value

            logger.debug('set %s value %s', names, final_value)
            # Not work on py2.6
            # value.update({name: final_value for name in names})
            final = {}
            for name in names:
                final[name] = final_value
            value.update(final)

        if self.auto2dashes:
            value['--'] = bool(argv_clone.dashes)

        self.clear()
        self.update(value)
        return value

    def check_flag_and_handler(self, token):
        for flag, handler in self.extra.items():
            if not callable(handler):
                continue
            find_it, _ = token.clone().break_for_option(
                (flag,), self.stdopt, self.attachvalue)
            if find_it:
                logger.info('find %s, auto handle it', flag)
                handler(self, flag)

    @staticmethod
    def help_handler(docpie, flag):
        '''Default `-h` handler. print help string and exit.

        By default, flag startswith `--` will print the full `doc`,
        otherwith, print "Usage" section and "Option" section.
        '''
        if flag.startswith('--'):
            print(docpie.doc)
        else:
            print(DocpieException.usage_str)
            print('')
            print(DocpieException.opt_str)
        sys.exit()

    @staticmethod
    def version_handler(docpie, flag):
        '''Default `-v` and `--version` handler. print the verison and exit.'''
        print(docpie.version)
        sys.exit()

    # @classmethod
    # Because it's divided from dict
    # json.dump(docpie, default=docpie.convert_2_dict) won't work
    # so convert to dict before JSONlizing
    def convert_2_dict(self):  # cls, self):
        '''Convert Docpie into a JSONlizable dict.

        Use it in this way:
        pie = Docpie(__doc__)
        json.dumps(pie.convert_2_dict())

        Note the `extra` info will be lost if you costomize that,
        because a function is not JSONlizable.
        '''
        config = {
            'stdopt': self.stdopt,
            'attachopt': self.attachopt,
            'attachvalue': self.attachvalue,
            'auto2dashes': self.auto2dashes,
            'case_sensitive': self.case_sensitive,
            'name': self.name,
            'help': self.help,
            'version': self.version
        }

        text = {
            'doc': self.doc,
            'usage_text': self.usage_text,
            'option_text': self.option_text,
        }

        option = [convert_2_dict(x) for x in OptionsShortcut._ref]

        usage = [convert_2_dict(x) for x in self.usages]

        return {
            '__class__': 'Docpie',
            '__config__': config,
            '__text__': text,
            'option': option,
            'usage': usage,
            'option_names': [list(x) for x in self.opt_names],
        }

    @classmethod
    def convert_2_docpie(cls, dic):
        '''Convert dict generated by `convert_2_dict` into Docpie instance

        You can do this:
        pie = Docpie(__doc__)
        clone_pie = json.loads(pie.convert_2_docpie(
            json.dumps(pie.convert_2_dict())
        ))

        Note if you changed `extra`, it will be lost. You need to change
        it again.
        '''
        assert dic['__class__'] == 'Docpie'
        config = dic['__config__']
        help = config.pop('help')
        version = config.pop('version')
        self = cls(None, **config)

        text = dic['__text__']
        self.doc = text['doc']
        self.usage_text = text['usage_text']
        self.option_text = text['option_text']
        DocpieException.usage_str = 'Usage:\n%s' % text['usage_text']
        DocpieException.option_str = 'Options:\n%s' % text['option_text']

        self.opt_names = [set(x) for x in dic['option_names']]
        self.set_config(help=help, version=version)

        OptionsShortcut._ref = [convert_2_object(x) for x in dic['option']]

        self.usages = [convert_2_object(x) for x in dic['usage']]

        return self

    def set_config(self, **config):
        '''Shadow all the current config.'''
        if 'stdopt' in config:
            self.stdopt = config.pop('stdopt')
        if 'attachopt' in config:
            self.attachopt = config.pop('attachopt')
        if 'attachvalue' in config:
            self.attachvalue = config.pop('attachvalue')
        if 'auto2dashes' in config:
            self.auto2dashes = config.pop('auto2dashes')
        if 'name' in config:
            self.name = config.pop('name')
        if 'help' in config:
            self.help = config.pop('help')
            self._set_or_remove_extra_handler(
                self.help, ('--help', '-h'), self.help_handler)
        if 'version' in config:
            self.version = config.pop('version')
            self._set_or_remove_extra_handler(
                self.version is not None,
                ('--version', '-v'),
                self.version_handler)
        if 'case_sensitive' in config:
            self.case_sensitive = config.pop('case_sensitive')
        if 'extra' in config:
            self.extra.update(config.pop('extra'))

        if config:  # should be empty
            raise ValueError(
                '%s is/are not accepted key argument(s)' % list(config.keys()))

    def _set_or_remove_extra_handler(self, set_handler, find_order, handler):
        for flag in find_order:
            alias = self.find_flag_alias(flag)
            if alias is not None:
                alias.add(flag)
                for each in alias:
                    if set_handler:
                        logger.info('set %s hanlder', each)
                        self.extra[each] = handler
                    else:
                        logger.info('remove %s hanlder', each)
                        self.extra.pop(each, None)
                break
        else:
            for flag in find_order:
                if set_handler:
                    logger.info('set %s hanlder', flag)
                    self.extra[flag] = handler
                else:
                    logger.info('remove %s hanlder', flag)
                    self.extra.pop(flag, None)

    def find_flag_alias(self, flag):
        '''Return alias set of a flag; return None if flag is not defined in
        "Options".
        '''
        for each in self.opt_names:
            if flag in each:
                result = set(each)  # a copy
                result.remove(flag)
                return result
        return None

    def set_auto_handler(self, flag, handler):
        assert flag.startswith('-') and flag not in ('-', '--')
        alias = self.find_flag_alias(flag) or []
        self.extra[flag] = handler
        for each in alias:
            self.extra[each] = handler

    def preview(self):
        '''A quick preview of docpie. Print all the parsed object'''
        print(('[Quick preview of Docpie %s]' % __version__).center(80, '='))
        print('')
        print(' str '.center(80, '-'))
        print('Usage:')
        for each in self.usages:
            print(each)
        print('\nOptions:')
        for each in OptionsShortcut._ref:
            print(each)

        print(' repr '.center(80, '-'))
        print('Usage:')
        for each in self.usages:
            print(repr(each))
        print('\nOptions:')
        for each in OptionsShortcut._ref:
            print(repr(each))
        print(' default handler '.center(80, '-'))
        for key, value in self.extra.items():
            print(key, value)

    def __str__(self):
        return '{%s}' % ',\n '.join('%r: %r' % i for i in sorted(self.items()))


def docpie(doc, argv=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           auto2dashes=True, name=None, case_sensitive=False, extra={}):
    """
    Parse `argv` based on command-line interface described in `doc`.

    `docpie` creates your command-line interface based on its
    description that you pass as `doc`. Such description can contain
    --options, <positional-argument>, commands, which could be
    [optional], (required), (mutually | exclusive) or repeated...
    Parameters
    ----------
    doc : str
        Description of your command-line interface.
    argv : list of str, optional
        Argument vector to be parsed. sys.argv is used if not
        provided.
    help : bool (default: True)
        Set to False to disable automatic help on -h or --help
        options.
    version : any object but None
        If passed, the object will be printed if --version is in
        `argv`.
    stdopt : bool (default: True)
        When it's True, long flag should only starts with --
    attachopt: bool (default: True)
        write/pass several short flag into one, e.g. -abc can mean -a -b -c.
        This only works when stdopt=True
    attachvalue: bool (default: True)
        allow you to write short flag and its value together,
        e.g. -abc can mean -a bc
    auto2dashes: bool (default: True)
        automaticly handle -- (which means "end of command line flag")
    name: str (default: None)
        the "name" of your program. In each of your "usage" the "name" will be
        ignored. By default docpie will ignore the first element of your
        "usage".
    case_sensitive: bool (default: False)
        specifies if it need case sensitive when matching
        "Usage:" and "Options:"
    extra: dict
        customize pre-handled options. see
        https://github.com/TylerTemp/docpie#auto-handler
        for more infomation.
    Returns
    -------
    args : dict
        A dictionary, where keys are names of command-line elements
        such as e.g. "--verbose" and "<path>", and values are the
        parsed values of those elements.
    Example
    -------
    >>> from docpie import docpie
    >>> doc = '''
    ... Usage:
    ...     my_program tcp <host> <port> [--timeout=<seconds>]
    ...     my_program serial <port> [--baud=<n>] [--timeout=<seconds>]
    ...     my_program (-h | --help | --version)
    ...
    ... Options:
    ...     -h, --help  Show this screen and exit.
    ...     --baud=<n>  Baudrate [default: 9600]
    ... '''
    >>> argv = ['my_program', 'tcp', '127.0.0.1', '80', '--timeout', '30']
    >>> docpie(doc, argv)
    {
     '--': False,
     '-h': False,
     '--baud': '9600',
     '--help': False,
     '--timeout': '30',
     '--version': False,
     '<host>': '127.0.0.1',
     '<port>': '80',
     'serial': False,
     'tcp': True}
    See also
    --------
    * Full documentation is available in README.md as well as online
      at https://github.com/TylerTemp/docpie#readme
    """

    kwargs = locals()
    argv = kwargs.pop('argv')
    pie = Docpie(**kwargs)
    pie.docpie(argv)
    return pie

if __name__ == '__main__':
    from docpie import bashlog
    bashlog.stdoutlogger(logger, logging.CRITICAL)
    doc = """Naval Fate.

Usage:
  naval_fate.py ship new <name>...
  naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
  naval_fate.py ship shoot <x> <y>
  naval_fate.py mine (set|remove) <x> <y> [--moored | --drifting]
  naval_fate.py (-h | --help)
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.

"""
    arguments = docpie(doc, version='Naval Fate 2.0')
    print(arguments)
