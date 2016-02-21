"""
Name:
    hide_options_in_help - example of costomize help handler

Usage:
    prog [options] run | exit | status
    prog [options] --deamon
    prog [dev-options]

Options:
    -h, --help     print this message
    -v, --version  print version
Dev Options:
    -d, --debug          open debug mode
    -o, --output=<file>  debug output file
"""

from docpie import Docpie
from sys import exit


class MyPie(Docpie):

    @staticmethod
    def help_handler(pie, flag):
        doc = pie.doc
        options = pie.option_sections
        # get the 'Dev Options' section
        dev = options['Dev']
        print(doc.replace(dev, ''))
        exit()


if __name__ == '__main__':
    pie = MyPie(__doc__)
    pie.docpie()
    print(pie)
