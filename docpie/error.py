class DocpieException(BaseException):
    usage_str = None
    opt_str = None


class DocpieExit(SystemExit, DocpieException):
    pass


class DocpieError(Exception, DocpieException):
    pass
