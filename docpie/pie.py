import sys
import re
import logging
import warnings

from docpie.error import DocpieException, DocpieExit, DocpieError
from docpie.parser import UsageParser, OptionParser, Parser
from docpie.element import convert_2_object, convert_2_dict
from docpie.token import Argv


try:
    StrType = basestring
except NameError:
    StrType = str

logger = logging.getLogger('docpie')


class Docpie(dict):

    # Docpie verison
    # it's not a good idea but it can avoid loop importing
    _version = '0.1.0'

    option_name = 'Options:'
    usage_name = 'Usage:'
    case_sensitive = False
    auto2dashes = True
    name = None
    help = True
    version = None
    stdopt = True
    attachopt = True
    attachvalue = True
    extra = {}
    opt_names = []
    long_opt_names = set()

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
            usage_str, self.usage_text = Parser.parse_section(
                doc, self.usage_name, self.case_sensitive)
            opt_str, self.option_text = Parser.parse_section(
                doc, self.option_name, self.case_sensitive)
            if self.usage_text is None:
                raise DocpieError('"Usage:" not found')

            self.options = OptionParser(opt_str, self.stdopt).get_chain()
            usages = UsageParser(
                usage_str, self.name, self.stdopt).get_chain()

            self.usages, self.opt_names, self.long_opt_names = \
                Parser.fix(self.options, usages)

            logger.debug(self.opt_names)

            self.set_config(help=help, version=version)

    def need_pickle(self):
        '''This function is deprecated, use pickle.dump() directly'''
        warnings.warn('This function is deprecated, '
                      'use pickle.dump(docpie_instance) directly',
                      DeprecationWarning)
        return self

    @staticmethod
    def restore_pickle(value):
        '''This function is deprecated, use pickle.load() directly'''
        warnings.warn('This function is deprecated, '
                      'use pickle.load() directly',
                      DeprecationWarning)
        if not isinstance(value, Docpie):
            raise ValueError('Not support old docpie pickle data')
        return value

    def docpie(self, argv=None):
        '''match the argv for each usages, return dict.

        if argv is None, it will use sys.argv instead.
        if argv is str, it will call argv.split() first.
        this function will check the options in self.extra and handle it first.
        Which means it may not try to match any usages because of the checking.
        '''
        if argv is None:
            argv = sys.argv
        elif isinstance(argv, StrType):
            argv = argv.split()

        token = Argv(argv[1:], self.auto2dashes,
                     self.stdopt, self.attachopt, self.attachvalue)

        # the things in extra may not be announced
        long_names = set(self.long_opt_names)
        long_names.update(
            filter(lambda x: x.startswith('--'), self.extra.keys()))
        error_msg = token.auto_expand(long_names)
        # check first, raise after
        # so `-hwhatever` can trigger `-h` first
        self.check_flag_and_handler(token)

        if self.option_text:
            help_msg = '%s\n%s' % (self.usage_text, self.option_text)
        else:
            help_msg = self.usage_text

        if error_msg is not None:
            raise DocpieExit('%s\n\n%s' % (error_msg, help_msg))
        options = self.options

        for each in self.usages:
            logger.debug('matching usage %s', each)
            argv_clone = token.clone()
            if each.match(argv_clone, options, False):
                logger.debug('matched usage %s, checking rest argv %s',
                             each, argv_clone)
                if (not argv_clone or
                        (argv_clone.auto_dashes and
                         list(argv_clone) == ['--'])):
                    argv_clone.check_dash()
                    logger.info('matched usage %s / %s', each, argv_clone)
                    matched = each
                    break
                each.reset()
                for opt in options:
                    opt.reset()
                logger.info('matching %s left %s, checking failed',
                            each, argv_clone)
                continue
            else:
                if each.error is not None:
                    logger.info('error in %s - %s', each, each.error)
                    raise DocpieExit(
                        '%s%s\n\n%s' % (
                        each.error,
                        ' Use `--help` to see more' if self.help else '',
                        self.usage_text))
                each.reset()
                for opt in options:
                    opt.reset()
                logger.info('failed matching usage %s / %s', each, argv_clone)
        else:
            logger.info('none matched')
            raise DocpieExit(self.usage_text)

        value = matched.get_value(options, False)
        logger.debug('get all matched value %s', value)
        rest = self.usages
        rest.remove(matched)

        for each in rest:  # add left command/argv
            default_values = each.get_sys_default_value(options, False)
            logger.debug('get rest values %s', default_values)
            common_keys = set(value).intersection(default_values)

            for key in common_keys:
                default = default_values[key]
                valued = value[key]
                logger.debug('%s: default(%s), matched(%s)',
                             key, default, valued)

                if ((default is not True and default is not False) and
                        isinstance(default, int)):
                    valued = int(valued)
                elif isinstance(default, list):
                    if valued is None:
                        valued = []
                    elif isinstance(valued, list):
                        pass
                    else:
                        valued = [valued]

                logger.debug('set %s as %s', key, valued)
                default_values[key] = valued

            value.update(default_values)

        logger.debug('merged rest values, now %s', value)

        # add left option, add default value
        for each in options:
            option = each[0]
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
                    elif (each.repeat or
                            (value_in_usage is not True and
                             value_in_usage is not False and
                             isinstance(value_in_usage, (int, list)))):
                        final_value = default.split()
                    else:
                        final_value = default
                else:
                    final_value = value_in_usage
                if option.ref is None and each.repeat:
                    final_value = int(final_value or 0)
            # just add this key-value. Note all option here never been matched
            else:
                ref = option.ref

                if default is not None:
                    if (each.repeat or
                            (this_value not in (True, False) and
                             isinstance(this_value, (int, list)))):
                        final_value = default.split()
                    else:
                        if ref is not None and max(ref.arg_range()) > 1:
                            final_value = default.split()
                        else:
                            final_value = default
                else:
                    if ref is not None:
                        arg_range = ref.arg_range()
                        # if min(arg_range) != 0:
                        #     # It requires at least a value
                        #     logger.info('%s expects value', option)
                        #     raise DocpieExit(DocpieException.usage_str)
                        if max(arg_range) == 1:
                            final_value = None
                        else:
                            assert max(arg_range) > 1
                            final_value = []
                    # ref is None
                    elif this_value is None:
                        final_value = 0 if each.repeat else False
                    else:
                        final_value = \
                            int(this_value) if each.repeat else this_value

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
            find_it, _, _ = token.clone().break_for_option((flag,))
            if find_it:
                logger.info('find %s, auto handle it', flag)
                handler(self, flag)

    @staticmethod
    def help_handler(docpie, flag):
        '''Default help(`--help`, `-h`) handler. print help string and exit.

        By default, flag startswith `--` will print the full `doc`,
        otherwith, print "Usage" section and "Option" section.
        '''
        if flag.startswith('--'):
            print(docpie.doc)
        else:
            print(docpie.usage_text)
            option_text = docpie.option_text
            if option_text:
                print('')
                print(option_text)
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
        You can use `set_config(extra={...})` to set it back.
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

        option = [convert_2_dict(x) for x in self.options]

        usage = [convert_2_dict(x) for x in self.usages]

        return {
            '__version__': self._version,
            '__class__': 'Docpie',
            '__config__': config,
            '__text__': text,
            'option': option,
            'usage': usage,
            'option_names': [list(x) for x in self.opt_names],
            'long_opt_names': list(self.long_opt_names)
        }

    @classmethod
    def convert_2_docpie(cls, dic):
        '''Convert dict generated by `convert_2_dict` into Docpie instance

        You can do this:
        pie = Docpie(__doc__)
        clone_pie = json.loads(pie.convert_2_docpie(
            json.dumps(pie.convert_2_dict())
        ))

        Note if you changed `extra`, it will be lost.
        You can use `set_config(extra={...})` to set it back.
        '''
        if '__version__' not in dic:
            raise ValueError('Not support old docpie data')

        data_version = int(dic['__version__'].replace('.', ''))
        this_version = int(cls._version.replace('.', ''))
        logger.debug('this: %s, old: %s', this_version, data_version)
        if data_version < this_version:
            raise ValueError('Not support old docpie data')
        assert dic['__class__'] == 'Docpie'
        config = dic['__config__']
        help = config.pop('help')
        version = config.pop('version')
        self = cls(None, **config)

        text = dic['__text__']
        self.doc = text['doc']
        self.usage_text = text['usage_text']
        self.option_text = text['option_text']

        self.opt_names = [set(x) for x in dic['option_names']]
        self.long_opt_names = set(dic['long_opt_names'])
        self.set_config(help=help, version=version)

        self.options = [convert_2_object(x) for x in dic['option']]

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
        '''Set pre-auto-handler for a flag.

        the handler must accept two argument: first the `pie` which
        referent to the current `Docpie` instance, second, the `flag`
        which is the flag found in `argv`.

        Different from `extra` argument, this will set the alias
        option you defined in `Option` section with the same
        behavior.
        '''
        assert flag.startswith('-') and flag not in ('-', '--')
        alias = self.find_flag_alias(flag) or []
        self.extra[flag] = handler
        for each in alias:
            self.extra[each] = handler

    def preview(self):
        '''A quick preview of docpie. Print all the parsed object'''
        print(('[Quick preview of Docpie %s]' % self._version).center(80, '='))
        print('')
        print(' str '.center(80, '-'))
        print('Usage:')
        for each in self.usages:
            print(each)
        print('\nOptions:')
        for each in self.options:
            print(each)

        print(' repr '.center(80, '-'))
        print('Usage:')
        for each in self.usages:
            print(repr(each))
        print('\nOptions:')
        for each in self.options:
            print(repr(each))
        print(' default handler '.center(80, '-'))
        for key, value in self.extra.items():
            print(key, value)

    def __str__(self):
        return '{%s}' % ',\n '.join('%r: %r' % i for i in sorted(self.items()))
