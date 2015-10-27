"""
NAME
   example - An example of ``docpie`` to write section title in ``man`` flavour

SYNOPSIS
   example [options]

DESCRIPTION
    This example shows how to customize the title of section
    by inherit ``usage_name`` and ``option_name``

OPTIONS
    -h, -?, --help    print this message
    -v, --version     print version

USAGE
    example -h/-?/--help can print the help message
    and example -v/--version can print the version
"""

from docpie import Docpie, __version__


class MyPie(Docpie):
    usage_name = 'SYNOPSIS'
    option_name = 'OPTIONS'

# Note: a bug here
# if `case_sensitive=False`, "OPTIONS" will also match "[options]"
# which is not correct

pie = MyPie(__doc__, case_sensitive=True, version=__version__)
pie.docpie()
print(pie)
