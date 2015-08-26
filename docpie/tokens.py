import logging

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

    def __init__(self, argv, auto2dashes=True):
        # self._full = argv
        self[:] = argv
        self.auto_dashes = auto2dashes
        self.dashes = False
        # self.index = 0

    def current(self, offset=0):
        return self[offset] if len(self) > offset else None

    def break_for_option(self, names, stdopt, attachvalue):
        sub_argv = None
        auto_dashes = self.auto_dashes
        for index, option in enumerate(self):
            if option == '--' and auto_dashes:
                return False, None
            for name in names:
                if option.startswith(name):

                    self.pop(index)
                    # `-flag=sth` -> `-flag =sth`
                    if not stdopt:
                        _, _, value = option.partition(name)
                        if value:
                            sub_argv = Argv([value],
                                            self.autodashes)
                        else:
                            sub_argv = None

                    # `-flag` -> `-f lag`
                    # `--flag=sth` -> `--flag sth`
                    # `--flag=` -> `--flag ""`
                    elif attachvalue:
                        _, _, value = option.partition(name)
                        if name.startswith('--') and value.startswith('='):
                            sub_argv = Argv([value[1:]],
                                            self.auto_dashes)
                        elif value:
                            sub_argv = Argv([value],
                                            self.auto_dashes)

                    logger.debug('find %s, sub_argv=%s', name, sub_argv)
                    return True, sub_argv

        return False, None

    def next(self, offset=0):

        return self.pop(offset) if len(self) > offset else None

    def check_dash(self):
        if not self:
            return
        if self[0] == '--':
            self.dashes = True

    def clone(self):
        result = Argv(self, self.auto_dashes)
        result.dashes = self.dashes
        return result

    def restore(self, ins):
        self[:] = ins
        self.dashes = ins.dashes

    def status(self):
        # return len(self)
        return list(self)

    def dump_value(self):
        return (list(self), self.dashes)

    def load_value(self, value):
        self[:], self.dashes = value
