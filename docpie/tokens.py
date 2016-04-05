import logging
from docpie.error import DocpieError, UnknownOptionExit, AmbiguousPrefixExit

logger = logging.getLogger('docpie.tokens')


class Token(list):
    _brackets = {'(': ')', '[': ']'}  # , '{': '}', '<': '>'}

    def next(self):
        return self.pop(0) if self else None

    def current(self):
        return self[0] if self else None

    def check_ellipsis_and_drop(self):
        if self and self[0] == '...':
            self.pop(0)
            return True
        return False

    def till_end_bracket(self, start):
        # start bracket should not in self
        end = self._brackets[start]
        count = dict.fromkeys(self._brackets, 0)
        count[start] = 1
        element = []
        while self:
            this = self.pop(0)
            for each_start, each_end in self._brackets.items():
                count[each_start] += (this == each_start)
                count[each_start] -= (this == each_end)
            if this == end and all(x == 0 for x in count.values()):
                if any(x < 0 for x in count.values()):
                    raise DocpieError("brackets not in pair")
                return element
            element.append(this)
        else:
            raise DocpieError("brackets not in pair")


class Argv(list):

    def __init__(self, argv, auto2dashes,
                 stdopt, attachopt, attachvalue, known={}):

        super(Argv, self).__init__(argv)
        self.auto_dashes = auto2dashes
        self.dashes = False
        # when this is on, only --option can try to match.
        self.option_only = False
        self.stdopt = stdopt
        self.attachopt = attachopt
        self.attachvalue = attachvalue
        self.error = None
        self.known = known

    def formal(self, options_first):
        names = self.known
        result = []
        skip = 0
        for index, each in enumerate(self):
            if skip:
                skip -= 1
                continue
            # first command/argument
            if (options_first and
                    (each in ('-', '--') or not each.startswith('-'))):
                result.extend((each, '--'))  # add '--' after it
                result.extend(self[index + 1:])
                break

            if each == '--' and self.auto_dashes:
                result.extend(self[index:])
                break

            if each == '-':
                result.append(each)
                continue

            expect_args = 0

            # this won't work when -abc, and it actually means -a -b -c,
            # but -b, -c is not defined
            if each.startswith('-') and not each.startswith('--'):
                if self.stdopt:
                    this_opt = each[:2]
                else:
                    this_opt = each

                if this_opt not in names:
                    self.error = UnknownOptionExit(
                        'Unknown option: %s.' % this_opt,
                        option=this_opt,
                        inside=each,
                    )
                    result.extend(self[index:])
                    break

                result.append(each)

                expect_args = names[this_opt]
                if this_opt != each:
                    expect_args = 0

            elif not each.startswith('--'):
                result.append(each)
                continue
            else:
                option, equal, value = each.partition('=')
                if option in names:
                    result.append(each)
                    if equal:
                        expect_args = 0
                    else:
                        expect_args = names[option]
                else:
                    possible = list(
                        filter(lambda x: x.startswith(option), names))
                    if not possible:
                        self.error = UnknownOptionExit(
                            'Unknown option: %s.' % option,
                            option=option,
                            inside=each,
                        )
                        result.extend(self[index:])
                        break
                        # Don't raise. It may be --help
                        # and the developer didn't announce in
                        # either Usage or Options
                        # logger.info('not found this argv %s', each)
                        # result.append(each)
                    elif len(possible) == 1:
                        replace = ''.join((possible[0], equal, value))
                        logger.debug('expand %s -> %s', each, replace)
                        result.append(replace)
                    else:
                        self.error = AmbiguousPrefixExit(
                            '%s is not a unique prefix: %s?' %
                            (option, ', '.join(possible)),
                            prefix=option,
                            ambiguous=possible
                        )
                        result.extend(self[index:])
                        break

            if expect_args:
                total_rest = self[index + 1:]
                if len(total_rest) < expect_args:
                    to_append = total_rest
                else:
                    to_append = total_rest[:expect_args]

                skip = len(to_append)
                result.extend(to_append)

        logger.debug('%s -> %s', self, result)
        self[:] = result
        return None

    def current(self, offset=0):
        return self[offset] if len(self) > offset else None

    def insert(self, index, object, from_=None):
        if self.auto_dashes and '--' in self:
            dashes_index = self.index('--')
        else:
            dashes_index = float('inf')

        fine = True
        if (object != '-' and
                object.startswith('-') and
                not object.startswith('--')):
            if self.stdopt:
                flag = object[:2]
            else:
                flag = object
            fine = (flag in self.known)
            logger.debug('%s has flag %s, is known: %s', object, flag, fine)

        if (index <= dashes_index and fine or
                index > dashes_index or
                fine):
            logger.debug('insert %s into %s at %s', object, self, index)
            return super(Argv, self).insert(index, object)

        logger.info('%s not in %s', flag, self.known)
        # self.error = 'Unknown option: %s.' % flag
        raise UnknownOptionExit('Unknown option: %s.' % flag,
                                option=flag,
                                inside=from_ or flag)

    def break_for_option(self, names):
        auto_dashes = self.auto_dashes
        stdopt = self.stdopt
        attachvalue = self.attachvalue
        for index, option in enumerate(self):
            if option == '--' and auto_dashes:
                return None, None, 0, option
            for name in names:
                if option.startswith(name):
                    value = None
                    self.pop(index)
                    # `-flag=sth` -> `-flag =sth`
                    if not stdopt:
                        _, _, value = option.partition(name)
                        if not value:
                            value = None

                    # `-flag` -> `-f lag`
                    # `--flag=sth` -> `--flag sth`
                    # `--flag=` -> `--flag ""`
                    # `-f` -> `-f None`
                    # `--flag-ext` -> `--flag -ext` -> not matched
                    # `--flag` -> `--flag None`
                    elif attachvalue:
                        _, _, value = option.partition(name)
                        if name.startswith('--'):
                            if value.startswith('='):
                                value = value[1:]
                            elif value:
                                return None, None, 0, None
                            else:
                                value = None
                        elif not value:
                            value = None

                    logger.debug('find %s, attached %s, index %s of %s',
                                 name, value, index, self)
                    return name, value, index, option

        return None, None, 0, None

    def next(self, offset=0):
        return self.pop(offset) if len(self) > offset else None

    def check_dash(self):
        if not self:
            return
        if self[0] == '--':
            self.dashes = True

    def clone(self):
        result = Argv(self, self.auto_dashes,
                      self.stdopt, self.attachopt, self.attachvalue)
        result.dashes = self.dashes
        result.option_only = self.option_only
        result.error = self.error
        result.known = self.known
        return result

    def restore(self, ins):
        self[:] = ins
        self.dashes = ins.dashes
        self.option_only = ins.option_only
        self.error = ins.error

    def status(self):
        # return len(self)
        return list(self)

    def dump_value(self):
        return list(self), self.dashes, self.option_only

    def load_value(self, value):
        self[:], self.dashes, self.option_only = value
