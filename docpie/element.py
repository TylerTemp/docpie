import logging
import re
from docpie.error import ExceptNoArgumentExit,\
                         ExpectArgumentExit, ExpectArgumentHitDoubleDashesExit
try:
    from itertools import product
except ImportError:
    # python 2.6
    def product(*args, **kwds):
        # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
        # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)

__all__ = ('Atom', 'Command', 'Argument', 'Option',
           'Unit', 'Required', 'Optional', 'OptionsShortcut', 'Either',
           'convert_2_dict', 'convert_2_object')

from docpie.tokens import Argv

logger = logging.getLogger('docpie.element')

try:
    StrType = basestring
except NameError:
    StrType = str
NoneType = type(None)


class Atom(object):

    flag_or_upper_re = re.compile(r'^(?P<hyphen>-{0,2})'
                                  r'($|[\da-zA-Z_][\da-zA-Z_\-]*$)')
    angular_bracket_re = re.compile(r'^<.*?>$')
    options_re = re.compile('\[(?P<title>[^\s\]]*)options\]', re.IGNORECASE)

    def __init__(self, *names, **kwargs):
        self.names = set(names)
        self.default = kwargs.get('default', None)
        self.value = None

    def _cache(get_class):
        cache_dic = {}

        def wrapped(cls, atom):
            if atom not in cache_dic:
                result = get_class(cls, atom)
                cache_dic[atom] = result
            return cache_dic[atom]

        return wrapped

    @classmethod
    @_cache
    def get_class(cls, atom):
        if atom in ('-', '--'):
            return Command, None
        elif atom == '-?':
            return Option, None

        opt = cls.options_re.match(atom)
        if opt is not None:
            title = opt.groupdict()['title']
            return OptionsShortcut, title

        m = cls.flag_or_upper_re.match(atom)
        if m:
            match = m.groupdict()
            if match['hyphen']:
                return Option, None
            elif atom.isupper():
                return Argument, None
            else:
                return Command, None
        elif cls.angular_bracket_re.match(atom):
            return Argument, None
        else:
            logger.debug('I guess %s is a Command' % atom)
            return Command, None

    def arg_range(self):
        return [1]

    def fix(self):
        return self
    fix_nest = fix
    fix_empty = fix

    @property
    def repeat(self):
        return False

    def dump_value(self):
        return self.value

    def load_value(self, value):
        self.value = value

    def expand(self):
        return [self]

    @classmethod
    def convert_2_dict(cls, obj):
        return {
            '__class__': obj.__class__.__name__,
            'names': tuple(obj.names),
            'default': obj.default,
        }

    @classmethod
    def convert_2_object(cls, dic, options, namedoptions):
        names = dic['names']
        cls_name = dic['__class__']
        assert cls_name in ('Option', 'Command', 'Argument')
        if cls_name == 'Option':
            # raise NotImplementedError('call Option.convert_2_object instead')
            return Option.convert_2_object(dic, options, namedoptions)
        elif cls_name == 'Command':
            cls = Command
        elif cls_name == 'Argument':
            cls = Argument
        default = dic['default']
        # Not work on py2.6
        # return cls(*names, default=default)
        return cls(*names, **{'default': default})

    def copy(self):
        return self.__class__(*self.names)

    def __str__(self):
        return '/'.join(self.names)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(self.names))

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        if not self.names.intersection(other.names):
            return False
        return True


class Option(Atom):
    long_re = re.compile(r'(?P<name>--[0-9a-zA-Z]*)(?P<eq>=?)(?P<value>.*)')

    def __init__(self, *names, **kwargs):
        # assert all(x.startswith('-') for x in names)
        super(Option, self).__init__(*names, **kwargs)
        self.ref = kwargs.get('ref', None)    # a instance, not a list
        # self.countable = False

    def get_value(self, appeared_only, in_repeat):
        # default = self.default
        names = self.names
        value = self.value
        ref = self.ref
        logger.debug('%s in repeat: %s', self, in_repeat)

        multi = (in_repeat or (value is not True and
                               value is not False and
                               not isinstance(value, StrType)))

        if ref is not None:
            max_value_num = -1 if in_repeat else max(ref.arg_range())
            multi = multi or (max_value_num > 1)
        else:
            max_value_num = 0

        if not value:  # False/None/0
            if max_value_num == 0:
                if value is None:
                    value = False
            elif max_value_num == 1:
                value = None
            else:
                value = []

            result = {}
            if appeared_only:
                value = -1  # means never appeared

            for name in names:
                result[name] = value
            logger.debug('%s returns its value %s', self, result)
            return result

        # has value, has ref
        if ref is not None:
            if max_value_num != 0:
                value = ref.get_flat_list_value()
                if max_value_num == 1:
                    assert len(value) < 2, value
                    value = value[0] if value else None

        # has value, no ref
        elif multi:
            if value is None:
                value = 0
            value = int(value)

        logger.debug('%s returns its value %s', self, value)
        # Not work on py2.6
        # return {name: value for name in names}
        result = {}
        for name in names:
            result[name] = value
        return result

    def get_sys_default_value(self, appeared_only, in_repeat):
        if appeared_only and self.value is None:
            return {}

        if in_repeat:
            if self.ref is not None:
                value = []
            else:
                value = 0
        elif self.ref is not None:
            arg_range = self.ref.arg_range()
            max_arg_num = max(arg_range)
            if max_arg_num == 0:
                value = False
            elif max_arg_num == 1:
                value = None
            else:
                value = []
        else:
            value = False
        # Not work on py2.6
        # return {name: value for name in self.names}
        result = {}
        for name in self.names:
            result[name] = value
        return result

    def match(self, argv, repeat_match):

        if not repeat_match and self.value:
            logger.debug('%s already has a value', self)
            return True

        current = argv.current()
        if current is None:
            logger.debug('no argv left')
            return False

        # self_value = self.dump_value()
        argv_value = argv.dump_value()
        # saver.save(self, argv)

        find_it, attached_value, index, _from = \
            argv.break_for_option(self.names)

        if find_it is None:
            logger.debug('not found matching %s in %s', self, argv)
            argv.load_value(argv_value)
            # saver.rollback(self, argv)
            return False

        if repeat_match:
            if self.value is None:
                self.value = 1
            else:
                self.value += 1
        else:
            self.value = True

        if self.ref is None:
            if attached_value is not None:
                if argv.stdopt and argv.attachopt and not find_it.startswith('--'):
                    logger.debug("%s put -%s pack to argv %s",
                                 self, attached_value, argv)
                    argv.insert(index, '-' + attached_value, _from)
                    logger.debug('%s matched %s / %s', self, self.value, argv)
                    return True
                logger.debug("%s doesn't have ref but argv is %s",
                             self, attached_value)
                # need restore?
                # self.load_value(self_value)
                # argv.load_value(argv_value)
                raise ExceptNoArgumentExit(
                    '%s must not have argument(s)' % '/'.join(self.names),
                    option=self.names,
                    hit=attached_value
                )
            logger.debug('%s matched %s / %s', self, self.value, argv)
            return True

        # option expects a value(e.g. `--flag=<sth>`), but the argv looks like
        # --flag -- sth
        # then it should fail
        if (attached_value is None and
                argv.current(index) == '--' and
                argv.auto_dashes and
                min(self.ref.arg_range()) > 0):
            logger.debug(
                '%s ref must fully match but failed because `--`', self)
            raise ExpectArgumentHitDoubleDashesExit(
                ('/'.join(self.names) +
                 ' requires argument(s) but hits "--".'),
                option=self.names
            )

        to_match_ref_argv = argv.clone()
        if attached_value is None:
            # --force=[<val>] <arg>
            # --force -- value
            if argv.current(index) == '--' and argv.auto_dashes:
                del to_match_ref_argv[:]
            else:
                to_match_ref_argv[:] = argv[index:]
                del argv[index:]
        else:
            to_match_ref_argv[:] = [attached_value]

        to_match_ref_argv.auto_dashes = False
        result = self.ref.match(to_match_ref_argv, repeat_match)

        if attached_value is not None and to_match_ref_argv:
            logger.debug('%s ref must fully match but failed for %s',
                        self, to_match_ref_argv)
            raise ExpectArgumentExit(
                '%s requires argument(s).' % ('/'.join(self.names)),
                option=self.names,
                hit=to_match_ref_argv[0] if to_match_ref_argv else None)

        if not result:
            logger.debug('%s ref match failed %s', self, to_match_ref_argv)

            raise ExpectArgumentExit(
                '%s requires argument(s).' % ('/'.join(self.names)),
                option=self.names,
                hit=to_match_ref_argv[0] if to_match_ref_argv else None)

            # saver.rollback(self, argv)
            # self.load_value(self_value)
            # argv.load_value(argv_value)
            # return False
        # merge argv
        if attached_value is None:
            argv.extend(to_match_ref_argv)
        logger.debug('%s matched %s / %s', self, self.value, argv)
        return True

    def reset(self):
        value = self.value
        if value is not None:
            if value is True or value is False:
                self.value = False
            else:
                self.value = 0

        if self.ref is not None:
            self.ref.reset()

    # Note: this is kind of tricky:
    # make it different from Unit(Command, Unit())
    def dump_value(self):
        ref = self.ref
        return {'self': self.value,
                'ref': None if ref is None else ref.dump_value()}

    def load_value(self, value):
        self.value = value['self']
        if self.ref is not None:
            self.ref.load_value(value['ref'])

    def merge_value(self, values):
        opt_values = [each['self'] for each in values]
        ref_values = [each['ref'] for each in values]

        if len(opt_values) == 1:
            assert len(ref_values) == 1
            result = {'self': opt_values[0], 'ref': ref_values[0]}
        else:
            opt_value = sum(filter(None, opt_values))
            if all(x is None for x in ref_values):
                ref_value = None
            else:
                ref_value = self.ref.merge_value(ref_values)
            result = {'self': opt_value, 'ref': ref_value}
        return result

    def matched(self):
        return self.value in ([], None, -1, 0)

    def copy(self):
        return self.__class__(*self.names, **{'ref': self.ref})

    @classmethod
    def convert_2_dict(cls, obj):
        ref = obj.ref
        result = super(Option, cls).convert_2_dict(obj)
        result['ref'] = (ref.convert_2_dict(ref) if ref is not None else None)
        return result

    @classmethod
    def convert_2_object(cls, dic, options, namedoptions):
        names = dic['names']
        cls_name = dic['__class__']
        assert cls_name == 'Option'
        default = dic['default']
        ref_value = dic['ref']
        ref = (None
               if ref_value is None
               else Unit.convert_2_object(ref_value, options, namedoptions))
        # Not work on py2.6
        # return cls(*names, default=default, ref=ref)
        return cls(*names, **{'default': default, 'ref': ref})

    def __str__(self):
        result = super(Option, self).__str__()
        if self.ref:
            return '`%s %s`' % (result, self.ref)
        return '`%s`' % result

    def __repr__(self):
        return 'Option(%s, ref=%r)' % (', '.join(self.names), self.ref)

    def __eq__(self, other):
        if not isinstance(other, Option):
            return False

        equal = self.names.intersection(other.names)

        if equal:
            equal = (self.ref == other.ref)

        return equal


class Command(Atom):

    def __init__(self, *names, **kwargs):
        # assert all(self.type(x) == self.COMMAND for x in names)
        super(Command, self).__init__(*names, **kwargs)
        self.value = False

    def reset(self):
        value = self.value
        if isinstance(value, bool):
            self.value = False
        else:
            self.value = 0
        # self.value = False

    def match(self, argv, repeat_match):

        if not repeat_match and self.value:
            logger.debug('%s already has a value %s', self, self.value)
            return True

        current = argv.current()
        if current is None:
            logger.debug('argv ran out before matching %s', self)
            return False

        if argv.option_only:
            logger.debug('option only, %s skipped.', self)
            return False

        skip = 0
        if current == '--':
            argv.check_dash()
            if argv.auto_dashes and argv.dashes:
                current = argv.current(1)
                skip = 1
            else:
                logger.debug('%s matching %s failed', self, current)
                return False

        if current not in self.names or Atom.get_class(current)[0] is Option:
            logger.debug('%s matching %s failed', self, current)
            return False

        if repeat_match:
            self.value += 1
        else:
            self.value = True

        # saver.save(self, argv)
        argv.next(skip)
        logger.debug('%s matched %s/%s', self, self.value, argv)
        return True

    def merge_value(self, values):
        if len(values) == 1:
            return values[0]
        else:
            return sum(filter(None, values))

    def get_value(self, appeared_only, in_repeat):
        if in_repeat:
            value = int(self.value)
        else:
            value = self.value

        # Not work on py2.6
        # return {name: value for name in self.names}
        result = {}
        for name in self.names:
            result[name] = value
        return result

    def get_sys_default_value(self, appeared_only, in_repeat):
        if in_repeat:
            value = 0
        else:
            value = False
        # Not work on py2.6
        # return {name: value for name in self.names}
        result = {}
        for name in self.names:
            result[name] = value
        return result

    def matched(self):
        return self.value


class Argument(Atom):

    def __init__(self, *names, **kwargs):
        super(Argument, self).__init__(*names, **kwargs)
        self.value = None

    def reset(self):
        if isinstance(self.value, list):
            del self.value[:]
        else:
            self.value = None

    def dump_value(self):
        value = self.value
        if isinstance(value, list):
            return list(value)
        return value

    def match(self, argv, repeat_match):

        if not repeat_match and (self.value is not None and self.value != []):
            logger.debug('%s already has a value %s', self, self.value)
            return True

        if argv.option_only:
            logger.debug('option only, %s skipped.', self)
            return False

        current = argv.current()
        if current is None:
            logger.debug('argv ran out when matching %s', self)
            return False

        if current == '--':
            argv.check_dash()
            if argv.auto_dashes and argv.dashes:
                current = argv.current(1)
                # nothing left
                if current is None:
                    logger.debug('argv %s ran out when matching %s',
                                 argv, self)
                    return False
                # force to be command/arg
                if repeat_match:
                    if self.value is None:
                        self.value = [current]
                    else:
                        self.value.append(current)

                else:
                    self.value = current

                # saver.save(self, argv)
                argv.next(1)
                logger.debug('%s matched %s/%s', self, self.value, argv)
                return True
            else:
                logger.debug('%s matching %s failed', self, current)
                return False

        # check if it's `--flag=sth`

        if current.startswith('--') and '=' in current:
            opt, value = current.split('=', 1)
            if Atom.get_class(opt)[0] is Option:
                logger.debug('%s matching %s failed', self, current)
                return False

        if Atom.get_class(current)[0] is Option:
            logger.debug('%s matching %s failed', self, current)
            return False

        if repeat_match:
            if self.value is None:
                self.value = [current]
            else:
                self.value.append(current)

        else:
            self.value = current

        # saver.save(self, argv)
        argv.next()
        logger.debug('%s matched %s/%s', self, self.value, argv)
        return True

    def get_value(self, appeared_only, in_repeat):
        value = self.value
        if in_repeat:
            if value is None:
                value = []
            elif not isinstance(value, list):
                value = [value]
        # Not work on py2.6
        # return {name: value for name in self.names}
        result = {}
        for name in self.names:
            result[name] = value
        return result

    def get_sys_default_value(self, appeared_only, in_repeat):
        if in_repeat:
            value = []
        else:
            value = None
        # Not work on py2.6
        # return {name: value for name in self.names}
        result = {}
        for name in self.names:
            result[name] = value
        return result

    def merge_value(self, values):
        if len(values) == 1:
            return values[0]
        else:
            result = []
            for each in values:
                if each is None:
                    pass
                elif isinstance(each, list):
                    result.extend(each)
                else:
                    result.append(each)
            return result

    def matched(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Argument):
            return True
        return False


class Unit(list):

    def __init__(self, *atoms, **kwargs):
        super(Unit, self).__init__(atoms)
        self.repeat = kwargs.get('repeat', False)

    def reset(self):
        for each in self:
            each.reset()

    def get_value(self, appeared_only, in_repeat):
        result = {}
        for each in self:
            this_result = each.get_value(appeared_only,
                                         in_repeat or self.repeat)
            repeated_keys = set(result).intersection(this_result)
            for key in repeated_keys:
                old_value = result[key]
                new_value = this_result[key]
                logger.debug('%s - old: %s, new: %s',
                             key, old_value, new_value)
                if (key.startswith('-') and
                        any(
                            isinstance(
                                x,
                                (int, NoneType))
                            for x in (old_value, new_value))):
                    # -1 - -1
                    if appeared_only and old_value == new_value == -1:
                        final_value = -1
                    elif set((old_value, new_value)).issubset((None, -1)):
                        final_value = []
                    # countable
                    else:
                        final_value = (old_value or 0) + (new_value or 0)
                elif all(isinstance(x, int) for x in (old_value, new_value)):
                    final_value = old_value + new_value
                else:
                    final_value = []
                    for each_value in (old_value, new_value):
                        if each_value is None:
                            pass
                        elif isinstance(each_value, list):
                            final_value.extend(each_value)
                        else:
                            final_value.append(each_value)
                logger.debug('merge %s value as %s', key, final_value)
                this_result[key] = final_value
            result.update(this_result)
        logger.debug('%s return value %s', self, result)
        return result

    def arg_range(self):
        if not self:
            return [0]

        all_range = (each.arg_range() for each in self)
        # all_range = list(all_range)
        producted = product(*all_range)
        # producted = list(producted)
        this_range = set(sum(x) for x in producted)

        if self.repeat:
            this_range.add(float('inf'))

        return list(this_range)

    def fix(self):
        if not self:
            return None
        if len(self) == 1:
            return self._fix_single_element()
        else:
            return self._fix_multi_element()

    def _fix_single_element(self):
        this_element = self[0].fix()
        # None, Atom, Unit, Either

        # None
        if this_element is None:
            return None

        # Atom, Unit, Either
        self[0] = this_element

        # Unit
        if isinstance(this_element, Unit):
            return self.fix_nest()

        # Atom
        return self

    def _fix_multi_element(self):
        result = []
        for each in self:
            fixed = each.fix()
            if fixed is not None:
                result.append(fixed)
        if not result:
            return None

        self[:] = result
        if len(result) == 1:
            return self._fix_single_element()
        else:
            return self

    def fix_nest(self):
        assert len(self) == 1, '%s need not fix nest' % self
        inside = self[0]
        if isinstance(inside, Unit):
            if len(inside) == 0:  # [()], ([]), (()), [[]]
                return None
            elif len(inside) == 1:  # [[sth]], ((sth)), ([sth]), [(sth)]
                innder_inside = inside[0].fix()
                if innder_inside is None:
                    return None
                if any(isinstance(x, Optional) for x in (self, inside)):
                    # [[sth]], ([sth]), [(sth)] -> (sth)
                    cls = Optional
                else:
                    # ((sth)) -> (sth)
                    cls = Required
                result = cls(innder_inside,
                             repeat=self.repeat or inside.repeat)
                return result.fix()

            repeat = self.repeat or inside.repeat
            # [(...)]
            if isinstance(self, Optional) and isinstance(inside, Required):
                fixed_inside = inside.fix()
                # [?]
                if fixed_inside is not inside:  # new
                    self[0] = fixed_inside
                    return self.fix()
                # inside does not need fix at all
                # [(...)] -> [(...)]
                return self
            # ([...]), ((...)), [[...]]
            else:
                inside.repeat = repeat
                return inside.fix()
        return self

    def push_option_ahead(self):
        options = []
        others = []
        for each in self:
            if isinstance(each, (Option, OptionsShortcut)):
                options.append(each)
            elif isinstance(each, Atom):
                others.append(each)
            elif each.push_option_ahead():
                options.append(each)
            else:
                others.append(each)
        self[:] = options + others
        return not others

    def _match_oneline(self, argv):
        # Though it's one line matching
        # It still need to deal with situation like:
        # `-b cmd1 -a cmd2 -b`
        # to match argv like `-b -a cmd1 cmd2 -b` or `-b cmd1 -a cmd2 -b`
        # it still check the line more than once

        old_status = None
        new_status = argv.status()
        matched_status = [isinstance(x, (Optional, OptionsShortcut))
                          for x in self]
        last_opt_or_arg = -1

        # the token is moving
        while old_status != new_status and argv:
            old_status = new_status
            for index, each in enumerate(self):
                if not argv:
                    logger.debug('argv run out when matching %s', each)
                    break

                # saver.save(each, argv)
                argv.option_only = (index <= last_opt_or_arg)
                result = each.match(argv, False)
                if result:
                    old_matching_status = matched_status[index]
                    matched_status[index] = True
                    if not old_matching_status:
                        if isinstance(each, (Argument, Command)):
                            last_opt_or_arg = index
                            logger.debug('set last matched %s in %s at %s',
                                         each, self, index)
                        # jump to the first, avoid
                        # `Usage: cmd --flag <arg>`
                        # matching `cmd --flag sth` fails.
                        # elif isinstance(each, Option):
                        #     logger.debug('jump')
                        #     break
            new_status = argv.status()

        logger.debug('out of loop matching %s, argv %s', self, argv)
        return matched_status

    # TODO: balance the value for `<a>... <b>`
    def match_repeat(self, argv):
        # saver.save(self, argv)
        old_status = None
        new_status = argv.status()
        full_match_count = 0
        history_values = [self.dump_value()]
        logger.debug('matching %s repeatedly, start: %s', self, argv)
        while old_status != new_status and argv:
            self.reset()
            # saver.save(self, argv)
            old_status = new_status
            result = self.match_oneline(argv)
            if result:
                full_match_count += 1
            else:
                break
            history_values.append(self.dump_value())
            new_status = argv.status()

        logger.debug('matching %s %s time(s)', self, full_match_count)
        if full_match_count:
            if len(history_values) == 1:
                merged_value = history_values[0]
            else:
                merged_value = self.merge_value(history_values)
            logger.debug('restore merged value %s for %s', merged_value, self)
            self.load_value(merged_value)
        else:
            assert len(history_values) == 1
            self.load_value(history_values[0])
        return full_match_count

    # TODO: better solution
    def balance_value_for_ellipsis_args(self):
        # This method can deal more complex situation now:
        # (<arg1> <arg2>)... <arg3>
        # <arg>... <arg2> cmd
        # <arg>... (cmd <arg2>) <arg3>
        # see: https://github.com/TylerTemp/docpie/blob/master/CHANGELOG.md#026

        ele_num = len(self)
        for index_1, element in enumerate(self, 1):
            if index_1 == ele_num:    # the last one
                return False

            if isinstance(element, OptionsShortcut):
                continue

            if not element.matched():
                logger.debug('%r not matched at all', element)
                return False

            # 1, 0, list
            ellipsis_args = self.can_lend_value(element)
            if ellipsis_args == 1:
                continue
            elif ellipsis_args == 0:
                return False
            else:
                rest = self[index_1:]
                assert rest, 'fixme: rest should not be empty'
                rest_args = self.can_borrow_value(rest)
                if rest_args is None:
                    return False
                if isinstance(element, Required):
                    return self.balance_required_value(ellipsis_args, rest_args)
                else:
                    return self.balance_optional_value(ellipsis_args, rest_args)
        return False

    def can_lend_value(self, element):
        # return 1 if should continue
        # return 0 if should stop
        # return flat elements list if it can borrow value

        if isinstance(element, Atom):
            return 1

        # then it's Unit
        if not element.repeat:
            return 1

        # then it's Unit & repeatable
        return self.lend_flat(element)

    def lend_flat(self, element):
        flat = []
        for each in element:
            if not isinstance(each, (Unit, Argument)):
                return 0
            if isinstance(each, Unit):
                # Should not contain repeatable anymore
                if each.repeat:
                    return 0
                flatted = self.lend_flat(each)
                if flatted in (0, 1):
                    return flatted
                flat.extend(flatted)
            elif isinstance(each, Argument):
                flat.append(each)
            else:
                return 0
        return flat

    def can_borrow_value(self, elements):
        flat = []
        for element in elements:
            if isinstance(element, Unit):
                if element.repeat:
                    return None

                if isinstance(element, Optional):
                    continue
                elif isinstance(element, Required):
                    flatted = self.can_borrow_value(element)
                    if flatted is None:
                        return None
                    flat.extend(flatted)
            elif element.matched():
                return None
            elif isinstance(element, (Command, Argument)):
                flat.append(element)

        # empty flat is meaningless
        return flat or None

    def balance_required_value(self, from_, to):
        supported_unit = len(from_)
        required_num = len(to)
        min_value_num = min(len(ele.value) for ele in from_)
        supported_times = min_value_num - 1
        required_times, rest = divmod(required_num, supported_unit)
        if rest or required_times > supported_times:
            logger.debug('Not suit to balance: %s -> %s', from_, to)
            return False
        backup = self.backup_before_balance(from_, to)
        collected_value = []
        for _ in range(required_times):
            this_value = []
            for ele in from_:
                this_value.append(ele.value.pop(-1))
            collected_value[:0] = this_value

        argv = Argv(collected_value, True, True, True, True)
        if not all(x.match(argv, False) for x in to):
            logger.debug('balance %s match failed', self)
            self.restore_for_balance(backup)
            return False

        logger.debug('balance %s succeed', self)
        return True

    def balance_optional_value(self, from_, to):
        required_num = len(to)
        min_value_num = min(len(ele.value) for ele in from_)

        backup = self.backup_before_balance(from_, to)

        collected_value = []
        for ele in from_[::-1]:
            if len(collected_value) == required_num:
                break

            this_value = ele.value
            this_value_num = len(this_value)
            if this_value_num != min_value_num:
                collected_value.insert(0, this_value.pop(-1))
                assert this_value_num - 1 == min_value_num, \
                    "fixme: re-collect value num is wrong"

        lack = required_num - len(collected_value)
        while lack:
            for ele in from_[::-1]:
                val = ele.value
                if len(val) == 1:
                    logger.debug('balance failed, at least leave one value')
                    self.restore_for_balance(backup)
                    return False
                collected_value.insert(0, val.pop(-1))
                lack -= 1
                if not lack:
                    break

        logger.debug('collected value %s', collected_value)
        argv = Argv(collected_value, True, True, True, True)
        if not all(x.match(argv, False) for x in to):
            logger.debug('balance match failed')
            self.restore_for_balance(backup)
            return False
        logger.debug('balance succeed')
        return True

    def backup_before_balance(self, from_, to):
        return ((from_, tuple(x.dump_value() for x in from_)),
                (to, tuple(x.dump_value() for x in to)))

    def restore_for_balance(self, backup):
        for each in backup:
            for ele, val in zip(*each):
                ele.load_value(val)

    # TODO: check if this is buggy
    def merge_value(self, value_list):
        result = []
        for index, values in enumerate(zip(*value_list)):
            ins = self[index]
            result.append(ins.merge_value(values))
        return result

    def dump_value(self):
        return [x.dump_value() for x in self]

    def load_value(self, value):
        for each, v in zip(self, value):
            each.load_value(v)

    def get_flat_list_value(self):
        result = []
        for each in self:
            if hasattr(each, 'get_flat_list_value'):
                result.extend(each.get_flat_list_value())
            else:
                assert isinstance(each, Argument)
                value = each.value
                # acturally argument has no default so far
                # default = each.default
                if value is None:
                    pass
                elif isinstance(value, list):
                    result.extend(value)
                else:
                    result.append(value)
        return result

    def get_sys_default_value(self, appeared_only, in_repeat):
        result = {}
        if in_repeat or self.repeat:
            for each in self:
                result.update(each.get_sys_default_value(appeared_only, True))
            return result

        for each in self:
            this_result = each.get_sys_default_value(appeared_only, False)
            common_keys = set(result).intersection(this_result)
            for key in common_keys:
                old_value = result[key]
                new_value = this_result[key]
                if all(isinstance(x, int)
                        for x in (old_value, new_value)):
                    this_result[key] = old_value + new_value
                else:
                    this_result[key] = []
            result.update(this_result)
        return result

    def expand(self):
        cls = self.__class__
        repeat = self.repeat
        if len(self) == 1 and isinstance(self[0], Either):
            return [cls(each, repeat=repeat) for each in self[0]]

        result = []
        for expanded in product(*(x.expand() for x in self)):
            # new = cls(*expanded, repeat=repeat)
            new = cls(*(e.copy() for e in expanded), repeat=repeat)
            result.append(new)

        return result

    def matched(self):
        return all(x.matched() for x in self)

    def copy(self):
        return self.__class__(*(x.copy() for x in self),
                              **{'repeat': self.repeat})

    @classmethod
    def convert_2_dict(cls, obj):
        return {
            '__class__': obj.__class__.__name__,
            'atoms': [x.convert_2_dict(x) for x in obj],
            'repeat': obj.repeat
        }

    @classmethod
    def convert_2_object(cls, dic, options, namedoptions):
        cls_name = dic['__class__']
        assert cls_name in ('Optional', 'Required')
        if cls_name == 'Optional':
            cls = Optional
        else:
            cls = Required
        atoms = [convert_2_object(x, options, namedoptions)
                 for x in dic['atoms']]
        repeat = dic['repeat']
        # Not work on py2.6
        # return cls(*atoms, repeat=repeat)
        return cls(*atoms, **{'repeat': repeat})

    def __eq__(self, other):
        if self.repeat != other.repeat:
            return False

        if len(self) != len(other):
            return False

        return all(ts == tt for ts, tt in zip(self, other))

    def __repr__(self):
        return '%s(%s%s)' % (self.__class__.__name__,
                             ', '.join(map(repr, self)),
                             ', repeat=True' if self.repeat else '')


class Required(Unit):

    def match(self, argv, repeat_match):

        if not (repeat_match or self.repeat):
            logger.debug('try to match %s once, %s', self, argv)
            result = self.match_oneline(argv)
            logger.debug('%s matching status: %s', self, result)
            return result

        logger.debug('try to match %s repeatedly', self)
        return self.match_repeat(argv)

    def match_oneline(self, argv):
        # saver.save(self, argv)
        self_value = self.dump_value()
        argv_value = argv.dump_value()

        matched_status = self._match_oneline(argv)

        if all(matched_status):
            logger.debug('%s matched', self)
            return True
        logger.debug('%s matching failed %s / %s', self, matched_status, argv)
        if self.balance_value_for_ellipsis_args():
            logger.debug('%s balace value succeed', self)
            return True

        self.load_value(self_value)
        argv.load_value(argv_value)
        # saver.rollback(self, argv)
        return False

    def __eq__(self, other):
        if not isinstance(other, Required):
            return False

        return super(Required, self).__eq__(other)

    def __str__(self):
        return '(%s)%s' % (' '.join(map(str, self)),
                           '...' if self.repeat else '')


class Optional(Unit):

    def arg_range(self):
        this_range = super(Optional, self).arg_range()
        if 0 not in this_range:
            this_range.append(0)
        return this_range

    def match_oneline(self, argv):
        # saver.save(self, argv)
        self._match_oneline(argv)
        return True

    def match(self, argv, repeat_match):
        repeat = repeat_match or self.repeat
        logger.debug('matching %s with %s%s',
                      self, argv, ', repeatedly' if repeat else '')
        func = (self.match_repeat if repeat else self.match_oneline)

        func(argv)
        return True

    def __eq__(self, other):
        if not isinstance(other, Optional):
            return False

        return super(Optional, self).__eq__(other)

    def __str__(self):
        if len(self) == 1:
            if isinstance(self[0], OptionsShortcut):
                if self.repeat:
                    return '%s...' % self[0]
                return str(self[0])

        return '[%s]%s' % \
               (' '.join(map(str, self)), '...' if self.repeat else '')


class OptionsShortcut(object):
    error = None

    def __init__(self, name, options):
        self._hide = set()
        self.name = name
        self.options = options

    def copy(self):
        ins = OptionsShortcut(
            self.name,
            self.options
        )
        ins.set_hide(self._hide)
        return ins

    def matched(self):
        return True

    def set_hide(self, names):
        self._hide.update(names)

    def get_hide(self):
        return self._hide

    def need_hide(self, *name):
        return self._hide.intersection(name)

    def arg_range(self):
        logger.debug('fixme: Unexpected call')
        return [0]

    def match(self, argv, repeat_match):
        options = self.options

        hide = self._hide
        logger.debug('[options]/%s/%s try matching %s', options, hide, argv)
        for each in filter(
                lambda x: not hide.intersection(x[0].names), options):

            if not argv:
                logger.debug('argv run out before matching [options] %s(-%s)',
                            options, self._hide)
                return True
            logger.debug('[options] try %s matching %s', each, argv)
            each.match(argv, repeat_match)

        return True

    def get_value(self, appeared_only, in_repeat):
        options = self.options
        hide = self._hide
        result = {}  # developer should ensure no same options in [options]
        for each in filter(
                lambda x: not hide.intersection(x[0].names), options):
            result.update(each.get_value(appeared_only, in_repeat))
        return result

    def get_sys_default_value(self, appeared_only, in_repeat):
        options = self.options
        hide = self._hide
        result = {}
        for each in filter(
                lambda x: not hide.intersection(x[0].names), options):
            result.update(each.get_sys_default_value(appeared_only, in_repeat))
        return result

    def reset(self):
        for each in self.options:
            each.reset()

    @property
    def repeat(self):
        return False

    def fix(self):
        if all(self.need_hide(*x[0].names) for x in self.options):
            return None
        return self

    def dump_value(self):
        return [x.dump_value() for x in self.options]

    def load_value(self, value):
        for ins, val in zip(self.options, value):
            ins.load_value(val)

    def merge_value(self, values):
        options = self.options
        result = []
        for index, value in enumerate(zip(values)):
            ins = options[index]
            result.append(ins.merge_value(value))

        return result

    def expand(self):
        # return [self]
        real = []
        for each in self.options:
            if self.need_hide(*each[0].names):
                continue
            real.append(each)
        return [Optional(*real)]

    @classmethod
    def convert_2_dict(cls, obj):
        return {
            '__class__': obj.__class__.__name__,
            'name': obj.name,
            # 'ref': [x.convert_2_dict(x) for x in obj.ref],
            'hide': tuple(obj._hide),
        }

    formal_title_re = re.compile('[\-_]')

    @classmethod
    def convert_2_object(cls, dic, options, namedoptions):
        assert dic['__class__'] == 'OptionsShortcut'

        if namedoptions:
            name = dic['name']
            formal_name = cls.formal_title_re.sub(' ', name.lower()).strip()
            for title, opts in options.items():
                if (formal_title_re.sub(' ', title.lower()).strip() ==
                        formal_name):
                    break
            else:
                raise AttributeError('Unexpected Error: %s not found' % name)
        else:
            opts = sum(options.values(), [])

        ins = OptionsShortcut(dic['name'], opts)
        ins.set_hide(dic['hide'])
        return ins

    # TODO: better behavior
    def __eq__(self, other):
        if isinstance(other, OptionsShortcut):
            return True
        return False

    def __str__(self):
        return '`[options]`'

    def __repr__(self):
        return 'OptionsShortcut()'


# branch
class Either(list):
    error = None

    def __init__(self, *branch):
        assert(all(isinstance(x, Unit) for x in branch))
        super(Either, self).__init__(branch)
        self.matched_branch = -1

    def fix(self):
        if not self:
            return None
        result = []
        for each in self:
            fixed = each.fix()
            if fixed is not None:
                result.append(fixed)
        if not result:
            return None
        self[:] = result
        return self.fix_argument_only()

    def fix_argument_only(self):
        '''
        fix_argument_only() -> Either or Unit(Argument)
        `<arg> | ARG | <arg3>` ->
            `Required(Argument('<arg>', 'ARG', '<arg3>'))`
        `[<arg>] | [ARG] | [<arg3>]` ->
            `Optional(Argument('<arg>', 'ARG', '<arg3>'))`
        `(<arg>) | [ARG]` -> not change, return self
        `-a | --better` -> not change
        '''
        # for idx, branch in enumerate(self):
        #     if isinstance(branch[0], Either):
        #         self[idx] = branch.fix()
        first_type = type(self[0])
        if first_type not in (Required, Optional):
            return self
        for branch in self:
            if not (len(branch) == 1 and
                    isinstance(branch, first_type) and
                    isinstance(branch[0], Argument)):
                logger.debug('fix %r not change', self)
                return self
        else:
            first = self[0][0]
            for each in self:
                first.names.update(each[0].names)
            result = first_type(first)
            logger.debug('fix %r -> %r', self, result)
            return result

    def arg_range(self):
        result = set()
        for each in self:
            result.update(each.arg_range())
        return list(result)


def convert_2_dict(obj):
    return obj.convert_2_dict(obj)


formal_title_re = re.compile('[\-_]')


def convert_2_object(dic, options, namedoptions):
    # never modify options
    cls_name = dic['__class__']
    name_to_method = {
        'Argument': Atom.convert_2_object,
        'Command': Atom.convert_2_object,
        'Option': Atom.convert_2_object,

        'Optional': Unit.convert_2_object,
        'Required': Unit.convert_2_object,
        'OptionsShourtcut': OptionsShortcut.convert_2_object,
    }

    if cls_name in name_to_method:
        method = name_to_method[cls_name]
        return method(dic, options, namedoptions)
    else:
        raise ValueError('%s can not be converted to object', dic)
