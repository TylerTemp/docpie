"""
An easy and Pythonic command-line interface parser.

 * http://docpie.comes.today
 * Repository and issue-tracker: https://github.com/TylerTemp/docpie
 * Licensed under terms of MIT license (see LICENSE)
 * Copyright (c) 2015-2016 TylerTemp, tylertempdev@gmail.com
"""

from docpie.pie import Docpie
from docpie.error import DocpieException, DocpieExit, DocpieError, \
                         UnknownOptionExit, ExceptNoArgumentExit, \
                         ExpectArgumentExit, \
                         ExpectArgumentHitDoubleDashesExit, \
                         AmbiguousPrefixExit
from logging import getLogger
import warnings

__all__ = ['docpie', 'Docpie',
           'DocpieException', 'DocpieExit', 'DocpieError',
           'UnknownOptionExit', 'ExceptNoArgumentExit',
           'ExpectArgumentExit', 'ExpectArgumentHitDoubleDashesExit',
           'AmbiguousPrefixExit',
           'logger']

# it's not a good idea but it can avoid loop importing
__version__ = Docpie._version

__timestamp__ = 1497537684.3899276  # last sumbit

logger = getLogger('docpie')


def docpie(doc, argv=None, help=True, version=None,
           stdopt=True, attachopt=True, attachvalue=True,
           auto2dashes=True, name=None, case_sensitive=False,
           optionsfirst=False, appearedonly=False, namedoptions=False,
           extra=None):
    """
    Parse `argv` based on command-line interface described in `doc`.

    `docpie` creates your command-line interface based on its
    description that you pass as `doc`. Such description can contain
    --options, <positional-argument>, commands, which could be
    [optional], (required), (mutually | exclusive) or repeated...
    Parameters
    ----------
    doc : str
        Description of your command-line interface.
    argv : list of str, optional
        Argument vector to be parsed. sys.argv is used if not
        provided.
    help : bool (default: True)
        Set to False to disable automatic help on -h or --help
        options.
    version : any object but None
        If passed, the object will be printed if --version is in
        `argv`.
    stdopt : bool (default: True)
        When it's True, long flag should only starts with --
    attachopt: bool (default: True)
        write/pass several short flag into one, e.g. -abc can mean -a -b -c.
        This only works when stdopt=True
    attachvalue: bool (default: True)
        allow you to write short flag and its value together,
        e.g. -abc can mean -a bc
    auto2dashes: bool (default: True)
        automaticly handle -- (which means "end of command line flag")
    name: str (default: None)
        the "name" of your program. In each of your "usage" the "name" will be
        ignored. By default docpie will ignore the first element of your
        "usage".
    case_sensitive: bool (deprecated / default: False)
        specifies if it need case sensitive when matching
        "Usage:" and "Options:"
    optionsfirst: bool (default: False)
        everything after first positional argument will be interpreted as
        positional argument
    appearedonly: bool (default: False)
        when set True, the options that never appear in argv will not
        be put in result. Note this only affect options
    extra: dict
        customize pre-handled options. See
        http://docpie.comes.today/document/advanced-apis/
        for more infomation.
    Returns
    -------
    args : dict
        A dictionary, where keys are names of command-line elements
        such as e.g. "--verbose" and "<path>", and values are the
        parsed values of those elements.
    Example
    -------
    >>> from docpie import docpie
    >>> doc = '''
    ... Usage:
    ...     my_program tcp <host> <port> [--timeout=<seconds>]
    ...     my_program serial <port> [--baud=<n>] [--timeout=<seconds>]
    ...     my_program (-h | --help | --version)
    ...
    ... Options:
    ...     -h, --help  Show this screen and exit.
    ...     --baud=<n>  Baudrate [default: 9600]
    ... '''
    >>> argv = ['my_program', 'tcp', '127.0.0.1', '80', '--timeout', '30']
    >>> docpie(doc, argv)
    {
     '--': False,
     '-h': False,
     '--baud': '9600',
     '--help': False,
     '--timeout': '30',
     '--version': False,
     '<host>': '127.0.0.1',
     '<port>': '80',
     'serial': False,
     'tcp': True}
    See also
    --------
    * Full documentation is available in README.md as well as online
      at http://docpie.comes.today/document/quick-start/
    """

    if case_sensitive:
        warnings.warn('`case_sensitive` is deprecated, `docpie` is always '
                      'case insensitive')

    kwargs = locals()
    argv = kwargs.pop('argv')
    pie = Docpie(**kwargs)
    pie.docpie(argv)
    return pie


if __name__ == '__main__':
    doc = """Naval Fate.

Usage:
  naval_fate.py ship new <name>...
  naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
  naval_fate.py ship shoot <x> <y>
  naval_fate.py mine (set|remove) <x> <y> [--moored | --drifting]
  naval_fate.py (-h | --help)
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.

"""
    arguments = docpie(doc, version='Naval Fate 2.0')
    print(arguments)
