class DocpieException(BaseException):
    '''Basic exception of docpie'''
    usage_str = None
    opt_str = None


class DocpieExit(SystemExit, DocpieException):
    '''Error in construction of usage-message by developer.'''


class DocpieError(Exception, DocpieException):
    '''Exit in case user invoked program with incorrect arguments.'''
