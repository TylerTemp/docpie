import logging
from docpie.error import DocpieError, DocpieExit

logger = logging.getLogger('docpie.tokens')

# it's named "tokens" because there is already "token" in python std lib


class Token(list):
    _brackets = {'(': ')', '[': ']'}  # , '{': '}', '<': '>'}

    def next(self):
        return self.pop(0) if self else None

    def current(self):
        return self[0] if self else None

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

    def __init__(self, argv, auto2dashes, stdopt, attachopt, attachvalue):
        # self._full = argv
        self[:] = argv
        self.auto_dashes = auto2dashes
        self.dashes = False
        # when this is on, only --option can try to match.
        self.option_only = False
        self.stdopt = stdopt
        self.attachopt = attachopt
        self.attachvalue = attachvalue

    def auto_expand(self, long_names):
        result = []
        for index, each in enumerate(self):
            if each == '--' and self.auto_dashes:
                result.extend(self[index:])
                break
            if not each.startswith('--') or each in long_names:
                result.append(each)
            else:
                option, equal, value = each.partition('=')
                if option == '--' or option in long_names:
                    result.append(each)
                else:
                    possible = list(
                        filter(lambda x: x.startswith(option), long_names))
                    if not possible:
                        return 'Unknown option: ' + each
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
                        return (
                            '%s is not a unique prefix: %s?' %
                            (option, ', '.join(possible))
                        )

        logger.debug('%s -> %s', self, result)
        self[:] = result
        return None

    def current(self, offset=0):
        return self[offset] if len(self) > offset else None

    def break_for_option(self, names):
        sub_argv = None
        auto_dashes = self.auto_dashes
        stdopt = self.stdopt
        attachvalue = self.attachvalue
        for index, option in enumerate(self):
            if option == '--' and auto_dashes:
                return False, None, 0
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
                    elif attachvalue:
                        _, _, value = option.partition(name)
                        if name.startswith('--') and value.startswith('='):
                            value = value[1:]
                        elif not value:
                            value = None

                    logger.debug('find %s, attached %s, index %s of %s',
                                 name, value, index, self)
                    return True, value, index

        return False, None, 0

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
        return result

    def restore(self, ins):
        self[:] = ins
        self.dashes = ins.dashes
        self.option_only = ins.option_only

    def status(self):
        # return len(self)
        return list(self)

    def dump_value(self):
        return (list(self), self.dashes, self.option_only)

    def load_value(self, value):
        self[:], self.dashes, self.option_only = value
