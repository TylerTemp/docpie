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
    autodash = True
    auto2dashes = True
    name = None
    help = True
    version = None

    def __init__(self, doc=None, **config):

        # set config first
        if config:
            self.set_config(config)

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

    def docpie(self, argv=None):
        if argv is None:
            argv = sys.argv
        elif isinstance(argv, StrType):
            argv = argv.split()

        token = Argv(argv[1:], self.autodash, self.auto2dashes)

        if self.help:
            self.check_help(token.clone())
        if self.version is not None:
            self.check_version(token.clone())

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

            logger.debug('%s/%s/%s', names, default, this_value)

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
                    if ref is not None and min(ref.arg_range()) != 0:
                        # It requires at least a value
                        logger.info('%s expects value', option)
                        raise DocpieExit(DocpieException.usage_str)
                    if this_value is None:
                        final_value = False
                    else:
                        final_value = this_value

            logger.debug('set %s value %s', names, final_value)
            value.update({name: final_value for name in names})

        if self.autodash:
            value['-'] = bool(argv_clone.dash)
        if self.auto2dashes:
            value['--'] = bool(argv_clone.dashes)

        self.clear()
        self.update(value)
        return value

    def check_help(self, token):
        self._check_flag_and_handle(
            token, ('-h',), self.short_help_handler)
        self._check_flag_and_handle(
            token, ('--help',), self.long_help_handler)

    def check_version(self, token):
        self._check_flag_and_handle(
            token, ('-v', '--version'), self.version_handler)

    def _check_flag_and_handle(self, token, flags, handler):
        find_it, _ = token.break_for_option(
            flags, self.stdopt, self.attachvalue)
        if find_it:
            logger.info('find %s, auto handle it', flags)
            return handler()

    def short_help_handler(self):
        print(DocpieException.usage_str)
        sys.exit()

    def long_help_handler(self):
        print(self.doc)
        sys.exit()

    def version_handler(self):
        print(self.version)
        sys.exit()

    # @classmethod
    # Because it's divided from dict
    # json.dump(docpie, default=docpie.convert_2_dict) won't work
    # so convert to dict before JSONlizing
    def convert_2_dict(self):  # cls, self):
        config = {
            'stdopt': self.stdopt,
            'attachopt': self.attachopt,
            'attachvalue': self.attachvalue,
            'autodash': self.autodash,
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
        }

    @classmethod
    def convert_2_docpie(cls, dic):
        assert dic['__class__'] == 'Docpie'
        self = cls(None, **dic['__config__'])

        text = dic['__text__']
        self.doc = text['doc']
        self.usage_text = text['usage_text']
        self.option_text = text['option_text']
        DocpieException.usage_str = 'Usage:\n%s' % text['usage_text']
        DocpieException.option_str = 'Options:\n%s' % text['option_text']

        OptionsShortcut._ref = [convert_2_object(x) for x in dic['option']]

        self.usages = [convert_2_object(x) for x in dic['usage']]

        return self

    def set_config(self, config):
        if 'stdopt' in config:
            self.stdopt = config.pop('stdopt')
        if 'attachopt' in config:
            self.attachopt = config.pop('attachopt')
        if 'attachvalue' in config:
            self.attachvalue = config.pop('attachvalue')
        if 'autodash' in config:
            self.autodash = config.pop('autodash')
        if 'auto2dashes' in config:
            self.auto2dashes = config.pop('auto2dashes')
        if 'name' in config:
            self.name = config.pop('name')
        if 'help' in config:
            self.help = config.pop('help')
        if 'version' in config:
            self.version = config.pop('version')
        if 'case_sensitive' in config:
            self.case_sensitive = config.pop('case_sensitive')

        if config:  # should be empty
            raise ValueError(
                '%s is/are not accepted key argument(s)' % list(config.keys()))

    def __str__(self):
        return '{%s}' % ',\n '.join('%r: %r' % i for i in sorted(self.items()))


def docpie(doc, argv=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           autodash=True, auto2dashes=True, name=None):

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
