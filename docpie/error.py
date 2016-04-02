class DocpieException(BaseException):
    """Basic exception of docpie"""


class DocpieExit(SystemExit, DocpieException):
    """Exit in case user invoked program with incorrect arguments."""


class UnknownOptionExit(DocpieExit):
    """Unknown options found in argv"""

    def __init__(self, message, option=None, inside=None):
        super(UnknownOptionExit, self).__init__(message)
        self.option = option
        self.inside = inside


class ExpectArgumentExit(DocpieExit):
    """Option expects argument but not found"""

    def __init__(self, message, option=None, hit=None):
        super(ExpectArgumentExit, self).__init__(message)
        self.option = option
        self.hit = hit


class ExpectArgumentHitDoubleDashesExit(ExpectArgumentExit):
    """Option expects argument but hits `--`"""
    def __init__(self, message, option=None):
        super(ExpectArgumentHitDoubleDashesExit, self).__init__(
            message, option, '--')


class AmbiguousPrefixExit(DocpieExit):
    """Long option has an ambiguous prefix"""
    def __init__(self, message, prefix=None, ambiguous=None):
        super(AmbiguousPrefixExit, self).__init__(message)
        self.prefix = prefix
        self.ambiguous = ambiguous


class DocpieError(Exception, DocpieException):
    """Error in construction of usage-message by developer."""
