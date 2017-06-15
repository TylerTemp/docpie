import sys
import logging

import warnings
from docpie.error import DocpieExit
from docpie.parser import UsageParser, OptionParser
from docpie.element import convert_2_object, convert_2_dict
from docpie.tokens import Argv

__all__ = ['Docpie']

try:
    StrType = basestring
except NameError:
    StrType = str

logger = logging.getLogger('docpie')


class Docpie(dict):

    # Docpie version
    # it's not a good idea but it can avoid loop importing
    _version = '0.3.5'

    option_name = 'Options:'
    usage_name = 'Usage:'
    doc = None

    case_sensitive = False
    auto2dashes = True
    name = None
    help = True
    version = None
    stdopt = True
    attachopt = True
    attachvalue = True
    options_first = False
    appeared_only = False
    extra = {}
    namedoptions = False

    opt_names = []
    opt_names_required_max_args = {}

    def __init__(self, doc=None, help=True, version=None,
                 stdopt=True, attachopt=True, attachvalue=True,
                 auto2dashes=True, name=None, case_sensitive=False,
                 optionsfirst=False, appearedonly=False, namedoptions=False,
                 extra=None):

        super(Docpie, self).__init__()

        if case_sensitive:
            warnings.warn('`case_sensitive` is deprecated, `docpie` is always '
                          'case insensitive')

        if extra is None:
            extra = {}
        else:
            extra = self._formal_extra(extra)

        # set config first
        self.set_config(
            stdopt=stdopt, attachopt=attachopt, attachvalue=attachvalue,
            auto2dashes=auto2dashes, name=name, case_sensitive=case_sensitive,
            optionsfirst=optionsfirst, appearedonly=appearedonly,
            namedoptions=namedoptions)

        self.help = help
        self.version = version
        self.extra = extra

        if doc is not None:
            self.doc = doc
            self._init()

    def _init(self):
        uparser = UsageParser(
            self.usage_name, self.case_sensitive,
            self.stdopt, self.attachopt, self.attachvalue, self.namedoptions)
        oparser = OptionParser(
            self.option_name, self.case_sensitive,
            self.stdopt, self.attachopt, self.attachvalue, self.namedoptions)

        uparser.parse_content(self.doc)
        self.usage_text = uparser.raw_content
        # avoid usage contains "Options:" word
        prefix, _, suffix = self.doc.partition(self.usage_text)

        oparser.parse(prefix + suffix)
        self.option_sections = oparser.raw_content
        self.options = oparser.instances

        uparser.parse(None, self.name, self.options)
        self.usages = uparser.instances

        self.opt_names_required_max_args = {}

        for opt_ins in uparser.all_options:
            if opt_ins.ref:
                # max_arg = max(opt_ins.arg_range())
                max_arg = max(opt_ins.ref.arg_range())
            else:
                max_arg = 0

            for each_name in opt_ins.names:
                self.opt_names_required_max_args[each_name] = max_arg

        self.opt_names = []
        for options in self.options.values():
            for each_option in options:
                self.opt_names.append(each_option[0].names)

        self.set_config(help=self.help,
                        version=self.version,
                        extra=dict(self.extra))

    def docpie(self, argv=None):
        """match the argv for each usages, return dict.

        if argv is None, it will use sys.argv instead.
        if argv is str, it will call argv.split() first.
        this function will check the options in self.extra and handle it first.
        Which means it may not try to match any usages because of the checking.
        """

        token = self._prepare_token(argv)
        # check first, raise after
        # so `-hwhatever` can trigger `-h` first
        self.check_flag_and_handler(token)

        if token.error is not None:
            # raise DocpieExit('%s\n\n%s' % (token.error, help_msg))
            self.exception_handler(token.error)

        try:
            result, dashed = self._match(token)
        except DocpieExit as e:
            self.exception_handler(e)

        # if error is not None:
        #     self.exception_handler(error)

        value = result.get_value(self.appeared_only, False)
        self.clear()
        self.update(value)
        if self.appeared_only:
            self._drop_non_appeared()

        logger.debug('get all matched value %s', self)
        rest = list(self.usages)  # a copy
        rest.remove(result)
        self._add_rest_value(rest)
        logger.debug('merged rest values, now %s', self)
        self._add_option_value()
        self._dashes_value(dashed)

        return dict(self)  # remove all other reference in this instance

    def _drop_non_appeared(self):
        for key, _ in filter(lambda k_v: k_v[1] == -1, dict(self).items()):
            self.pop(key)

    def _add_rest_value(self, rest):
        for each in rest:
            default_values = each.get_sys_default_value(
                self.appeared_only, False)
            logger.debug('get rest values %s -> %s', each, default_values)
            common_keys = set(self).intersection(default_values)

            for key in common_keys:
                default = default_values[key]
                valued = self[key]
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

            self.update(default_values)

    def _add_option_value(self):
        # add left option, add default value
        for options in self.options.values():
            for each in options:
                option = each[0]
                names = option.names
                default = option.default
                this_value = option.value

                logger.debug('%s/%s/%s', option, default, this_value)

                name_in_value = names.intersection(self)
                if name_in_value:  # add default if necessary
                    one_name = name_in_value.pop()
                    logger.debug('in names, pop %s, self %s', one_name, self)
                    value_in_usage = self[one_name]
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
                elif self.appeared_only:
                    continue
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
                            #     logger.debug('%s expects value', option)
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
                final = {}
                for name in names:
                    final[name] = final_value
                self.update(final)

    def _dashes_value(self, dashes):
        result = self['--'] if '--' in self else dashes
        if self.options_first:
            if result is True:
                result = False
            elif result is False:
                pass
            elif isinstance(result, int):
                result = max(0, result - 1)

        if self.auto2dashes:
            result = bool(result)

        self['--'] = result

    def _prepare_token(self, argv):
        if argv is None:
            argv = sys.argv
        elif isinstance(argv, StrType):
            argv = argv.split()

        # the things in extra may not be announced
        all_opt_requried_max_args = dict.fromkeys(self.extra, 0)
        all_opt_requried_max_args.update(self.opt_names_required_max_args)
        token = Argv(argv[1:], self.auto2dashes or self.options_first,
                     self.stdopt, self.attachopt, self.attachvalue,
                     all_opt_requried_max_args)
        none_or_error = token.formal(self.options_first)
        logger.debug('formal token: %s; error: %s', token, none_or_error)
        if none_or_error is not None:
            return self.exception_handler(none_or_error)
        return token

    def _match(self, token):
        for each in self.usages:
            logger.debug('matching usage %s', each)
            argv_clone = token.clone()
            if each.match(argv_clone, False):
                logger.debug('matched usage %s, checking rest argv %s',
                             each, argv_clone)
                if (not argv_clone or
                        (argv_clone.auto_dashes and
                         list(argv_clone) == ['--'])):
                    argv_clone.check_dash()
                    logger.debug('matched usage %s / %s', each, argv_clone)
                    return each, argv_clone.dashes

                logger.debug('matching %s left %s, checking failed',
                            each, argv_clone)

            each.reset()
            logger.debug('failed matching usage %s / %s', each, argv_clone)

        else:
            logger.debug('none matched')
            raise DocpieExit(None)

    def check_flag_and_handler(self, token):
        need_arg = [name for name, expect in
                    self.opt_names_required_max_args.items() if expect != 0]
        options = set()

        for ele in token:
            if self.auto2dashes and ele == '--':
                break
            if ele.startswith('-') and ele != '-':
                options.add(ele)

        for inputted in options:

            found = False
            for auto, handler in self.extra.items():
                if not callable(handler):
                    continue

                if auto.startswith('--') and inputted.startswith('--'):
                    logger.debug('check %s for %s', inputted, auto)
                    if '=' in inputted:
                        inputted = inputted.split('=', 1)[0]
                    if inputted == auto:
                        found = True
                        break

                elif auto[1] != '-' and inputted[1] != '-':
                    logger.debug('check %s for %s', inputted, auto)
                    if self.stdopt:
                        attachopt = self.attachopt
                        break_upper = False
                        for index, attached_name in enumerate(inputted[1:]):
                            if not attachopt and index > 0:
                                break

                            logger.debug('check %s for %s', attached_name, auto)

                            stacked_name = '-' + attached_name
                            if stacked_name == auto:
                                found = True
                                logger.debug('find %s in %s', auto, inputted)

                            if stacked_name in need_arg:
                                break_upper = True
                                break

                        if found or break_upper:  # break upper loop
                            break
                    else:
                        found = (inputted == auto)

            if found:
                logger.debug('find %s, auto handle it', auto)
                handler(self, auto)

    def exception_handler(self, error):
        logger.debug('handling %r', error)

        if self.option_sections:
            help_msg = ('%s\n%s' %
                        (self.usage_text,
                         '\n'.join(self.option_sections.values())))
        else:
            help_msg = self.usage_text

        args = list(error.args)
        message = args[0]
        if message is not None:
            help_msg = '%s\n\n%s' % (message, help_msg)

        args[0] = help_msg
        error = self.clone_exception(error, args)
        error.usage_text = self.usage_text
        error.option_sections = self.option_sections
        error.msg = message
        logger.debug('re-raise %r', error)
        raise error

    @staticmethod
    def clone_exception(error, args):
        """
        return a new cloned error

        when do:

        ```
        try:
            do_sth()
        except BaseException as e:
            handle(e)

        def handle(error):
            # do sth with error
            raise e  # <- won't work!

        This can generate a new cloned error of the same class

        Parameters
        ----------
        error: the caught error
        args: the new args to init the cloned error

        Returns
        -------
        new error of the same class
        """
        new_error = error.__class__(*args)
        new_error.__dict__ = error.__dict__
        return new_error

    @staticmethod
    def help_handler(docpie, flag):
        """Default help(`--help`, `-h`) handler. print help string and exit.

        By default, flag startswith `--` will print the full `doc`,
        otherwith, print "Usage" section and "Option" section.
        """
        if flag.startswith('--'):
            print(docpie.doc)
        else:
            print(docpie.usage_text)
            option_sections = docpie.option_sections
            if option_sections:
                print('')
                print('\n'.join(option_sections.values()))
        sys.exit()

    @staticmethod
    def version_handler(docpie, flag):
        """Default `-v` and `--version` handler. print the verison and exit."""
        print(docpie.version)
        sys.exit()

    # Because it's divided from dict
    # json.dump(docpie, default=docpie.convert_2_dict) won't work
    # so convert to dict before JSONlizing
    def to_dict(self):  # cls, self):
        """Convert Docpie into a JSONlizable dict.

        Use it in this way:
        pie = Docpie(__doc__)
        json.dumps(pie.convert_2_dict())

        Note the `extra` info will be lost if you costomize that,
        because a function is not JSONlizable.
        You can use `set_config(extra={...})` to set it back.
        """
        config = {
            'stdopt': self.stdopt,
            'attachopt': self.attachopt,
            'attachvalue': self.attachvalue,
            'auto2dashes': self.auto2dashes,
            'case_sensitive': self.case_sensitive,
            'namedoptions': self.namedoptions,
            'appearedonly': self.appeared_only,
            'optionsfirst': self.options_first,
            'option_name': self.option_name,
            'usage_name': self.usage_name,
            'name': self.name,
            'help': self.help,
            'version': self.version
        }

        text = {
            'doc': self.doc,
            'usage_text': self.usage_text,
            'option_sections': self.option_sections,
        }

        # option = [convert_2_dict(x) for x in self.options]

        option = {}
        for title, options in self.options.items():
            option[title] = [convert_2_dict(x) for x in options]

        usage = [convert_2_dict(x) for x in self.usages]

        return {
            '__version__': self._version,
            '__class__': 'Docpie',
            '__config__': config,
            '__text__': text,
            'option': option,
            'usage': usage,
            'option_names': [list(x) for x in self.opt_names],
            'opt_names_required_max_args': self.opt_names_required_max_args
        }

    convert_2_dict = convert_to_dict = to_dict

    @classmethod
    def from_dict(cls, dic):
        """Convert dict generated by `convert_2_dict` into Docpie instance

        You can do this:
        pie = Docpie(__doc__)
        clone_pie = json.loads(pie.convert_2_docpie(
            json.dumps(pie.convert_2_dict())
        ))

        Note if you changed `extra`, it will be lost.
        You can use `set_config(extra={...})` to set it back.
        """
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
        option_name = config.pop('option_name')
        usage_name = config.pop('usage_name')
        self = cls(None, **config)
        self.option_name = option_name
        self.usage_name = usage_name

        text = dic['__text__']
        self.doc = text['doc']
        self.usage_text = text['usage_text']
        self.option_sections = text['option_sections']

        self.opt_names = [set(x) for x in dic['option_names']]
        self.opt_names_required_max_args = dic['opt_names_required_max_args']
        self.set_config(help=help, version=version)
        self.options = o = {}
        for title, options in dic['option'].items():
            opt_ins = [convert_2_object(x, {}, self.namedoptions)
                       for x in options]
            o[title] = opt_ins

        self.usages = [convert_2_object(x, self.options, self.namedoptions)
                       for x in dic['usage']]

        return self

    convert_2_docpie = convert_to_docpie = from_dict

    def set_config(self, **config):
        """Shadow all the current config."""
        reinit = False
        if 'stdopt' in config:
            stdopt = config.pop('stdopt')
            reinit = (stdopt != self.stdopt)
            self.stdopt = stdopt
        if 'attachopt' in config:
            attachopt = config.pop('attachopt')
            reinit = reinit or (attachopt != self.attachopt)
            self.attachopt = attachopt
        if 'attachvalue' in config:
            attachvalue = config.pop('attachvalue')
            reinit = reinit or (attachvalue != self.attachvalue)
            self.attachvalue = attachvalue
        if 'auto2dashes' in config:
            self.auto2dashes = config.pop('auto2dashes')
        if 'name' in config:
            name = config.pop('name')
            reinit = reinit or (name != self.name)
            self.name = name
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
            case_sensitive = config.pop('case_sensitive')
            reinit = reinit or (case_sensitive != self.case_sensitive)
            self.case_sensitive = case_sensitive
        if 'optionsfirst' in config:
            self.options_first = config.pop('optionsfirst')
        if 'appearedonly' in config:
            self.appeared_only = config.pop('appearedonly')
        if 'namedoptions' in config:
            namedoptions = config.pop('namedoptions')
            reinit = reinit or (namedoptions != self.namedoptions)
            self.namedoptions = namedoptions
        if 'extra' in config:
            self.extra.update(self._formal_extra(config.pop('extra')))

        if config:  # should be empty
            raise ValueError(
                '`%s` %s not accepted key argument%s' % (
                    '`, `'.join(config),
                    'is' if len(config) == 1 else 'are',
                    '' if len(config) == 1 else 's'
                ))

        if self.doc is not None and reinit:
            logger.warning('You changed the config that requires re-initialized'
                           ' `Docpie` object. Create a new one instead')
            self._init()

    def _formal_extra(self, extra):
        result = {}
        for keys, value in extra.items():
            if isinstance(keys, StrType):
                keys = [keys]

            result.update((k, value) for k in keys)

        return result

    def _set_or_remove_extra_handler(self, set_handler, find_order, handler):
        for flag in find_order:
            alias = self.find_flag_alias(flag)
            if alias is not None:
                alias.add(flag)
                for each in alias:
                    if set_handler:
                        logger.debug('set %s hanlder %s', each, handler)
                        self.extra[each] = handler
                    else:
                        logger.debug('remove %s hanlder', each)
                        _hdlr = self.extra.pop(each, None)
                        logger.debug('%s handler %s removed', each, _hdlr)
                break
        else:
            for flag in find_order:
                if set_handler:
                    logger.debug('set %s hanlder', flag)
                    self.extra[flag] = handler
                else:
                    logger.debug('remove %s hanlder', flag)
                    self.extra.pop(flag, None)

    def find_flag_alias(self, flag):
        """Return alias set of a flag; return None if flag is not defined in
        "Options".
        """
        for each in self.opt_names:
            if flag in each:
                result = set(each)  # a copy
                result.remove(flag)
                return result
        return None

    def set_auto_handler(self, flag, handler):
        """Set pre-auto-handler for a flag.

        the handler must accept two argument: first the `pie` which
        referent to the current `Docpie` instance, second, the `flag`
        which is the flag found in `argv`.

        Different from `extra` argument, this will set the alias
        option you defined in `Option` section with the same
        behavior.
        """
        assert flag.startswith('-') and flag not in ('-', '--')
        alias = self.find_flag_alias(flag) or []
        self.extra[flag] = handler
        for each in alias:
            self.extra[each] = handler

    def preview(self, stream=sys.stdout):
        """A quick preview of docpie. Print all the parsed object"""

        write = stream.write

        write(('[Quick preview of Docpie %s]' % self._version).center(80, '='))
        write('\n')

        write(' sections '.center(80, '-'))

        write('\n')
        write(self.usage_text)
        write('\n')
        option_sections = self.option_sections
        if option_sections:
            write('\n')
            write('\n'.join(option_sections.values()))
        write('\n')

        write(' str '.center(80, '-'))
        write('\n[%s]\n' % self.usage_name)
        for each in self.usages:
            write('    %s\n' % each)
        write('\n[Options:]\n\n')
        for title, sections in self.options.items():
            if title:
                full_title = '%s %s' % (title, self.option_name)
            else:
                full_title = self.option_name

            write(full_title)
            write('\n')

            for each in sections:
                write('    %s\n' % each)

            write('\n')

        write(' repr '.center(80, '-'))
        write('\n[%s]\n' % self.usage_name)
        for each in self.usages:
            write('    %r\n' % each)
        write('\n[Options:]\n\n')
        for title, sections in self.options.items():
            if title:
                full_title = '%s %s' % (title, self.option_name)
            else:
                full_title = self.option_name

            write(full_title)
            write('\n')

            for each in sections:
                write('    %r\n' % each)

            write('\n')

        write(' auto handlers '.center(80, '-'))
        write('\n')
        for key, value in self.extra.items():
            write('%s %s\n' % (key, value))

    def __str__(self):
        return '{%s}' % ',\n '.join('%r: %r' % i for i in sorted(self.items()))
