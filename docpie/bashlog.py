'''A simple wrapper of logging that support color prompt on Linux'''
import sys
import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

__all__ = ['getlogger', 'stdoutlogger', 'filelogger', 'streamlogger',
           'ColorFormatter',
           'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
# Note: Only terminal which support color can use this
# Don't use it in file logger

if type('') is not type(b''):
    # def u(s):
        # return s
    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    # def u(s):
        # return s.decode('unicode_escape')
    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring

_TO_UNICODE_TYPES = (unicode_type, type(None))


def _stderr_supports_color():
    if sys.platform.startswith('win32'):
        return False
    if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        return True
    return False


def to_unicode(value):
    """Converts a string argument to a unicode string.

    If the argument is already a unicode string or None, it is returned
    unchanged.  Otherwise it must be a byte string and is decoded as utf8.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    if not isinstance(value, bytes_type):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.decode("utf-8")


def _safe_unicode(s):
    try:
        return to_unicode(s)
    except UnicodeDecodeError:
        return repr(s)


class ColorFormatter(logging.Formatter):
    RS = "\033[0m"     # reset
    HC = "\033[1m"     # hicolor
    UL = "\033[4m"     # underline
    INV = "\033[7m"    # inverse background and foreground
    FBLK = "\033[30m"  # foreground black
    FRED = "\033[31m"  # foreground red
    FGRN = "\033[32m"  # foreground green
    FYEL = "\033[33m"  # foreground yellow
    FBLE = "\033[34m"  # foreground blue
    FMAG = "\033[35m"  # foreground magenta
    FCYN = "\033[36m"  # foreground cyan
    FWHT = "\033[37m"  # foreground white
    BBLK = "\033[40m"  # background black
    BRED = "\033[41m"  # background red
    BGRN = "\033[42m"  # background green
    BYEL = "\033[43m"  # background yellow
    BBLE = "\033[44m"  # background blue
    BMAG = "\033[45m"  # background magenta
    BCYN = "\033[46m"  # background cyan
    BWHT = "\033[47m"  # background white

    DEFAULT_FORMAT = (
        '%(all)s%(color)s'
        '[%(levelname)1.1s %(lineno)3d %(asctime)s %(module)s:%(funcName)s]'
        '%(end_color)s %(message)s')
    DEFAULT_DATE_FORMAT = '%y%m%d %H:%M:%S'
    DEFAULT_COLORS = {
        logging.DEBUG:      FGRN,
        logging.INFO:       FBLE,
        logging.WARNING:    FYEL,
        logging.ERROR:      FRED,
        logging.CRITICAL:   FRED,
    }

    def __init__(self, color=True, fmt=DEFAULT_FORMAT,
                 datefmt=DEFAULT_DATE_FORMAT, colors=DEFAULT_COLORS):

        super(ColorFormatter, self).__init__(fmt, datefmt)

        self._color = (color and _stderr_supports_color())
        self._normal = self.RS if self._color else ''

        self._colors = colors if self._color else {}
        self._fmt = fmt

    def format(self, record):
        try:
            message = record.getMessage()
            assert isinstance(message, basestring_type)
            record.message = _safe_unicode(message)
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)

        record.asctime = self.formatTime(record, self.datefmt)

        record.all = ''
        if record.levelno in self._colors:
            if record.levelno >= logging.CRITICAL:
                record.all = self.HC+self.UL
            record.color = self._colors[record.levelno]
            record.end_color = self._normal
        else:
            record.color = record.end_color = ''

        formatted = self._fmt % record.__dict__

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # exc_text contains multiple lines.  We need to _safe_unicode
            # each line separately so that non-utf8 bytes don't cause
            # all the newlines to turn into '\n'.
            lines = [formatted.rstrip()]
            lines.extend(_safe_unicode(ln)
                         for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)

        return formatted.replace("\n", "\n    ")


def _getlogger(hdlr, logger=None, level=None, color=True):
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)
    hdlr.setFormatter(ColorFormatter(color=color))
    logger.addHandler(hdlr)
    if level is not None:
        logger.setLevel(level)
    return logger


def stdoutlogger(logger=None, level=None, color=True):
    hdlr = logging.StreamHandler(sys.stdout)
    return _getlogger(hdlr, logger, level, color)


def stderrlogger(logger=None, level=None, color=True):
    hdlr = logging.StreamHandler(sys.stderr)
    return _getlogger(hdlr, logger, level, color)


def filelogger(file, logger=None, level=None):
    hdlr = logging.FileHandler(file)
    return _getlogger(hdlr, logger, level, False)


def streamlogger(stream, logger=None, level=None, color=True):
    hdlr = logging.StreamHandler(stream)
    return _getlogger(hdlr, logger, level, color)

getlogger = stdoutlogger

if __name__ == '__main__':
    logger = getlogger('test1', DEBUG)
    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.error('error')
    logger.critical('critical')
    logger = getlogger('test2', DEBUG, False)
    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.error('error')
    logger.critical('critical')
