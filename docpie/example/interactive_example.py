'''
This example uses docopt with the built in cmd module to demonstrate an
interactive command application.
Usage:
    my_program tcp <host> <port> [--timeout=<seconds>]
    my_program serial <port> [--baud=<n>] [--timeout=<seconds>]
    my_program (-i | --interactive)
    my_program (-h | --help | --version)

Options:
    -i, --interactive  Interactive Mode
    -h, --help         Show this screen and exit.
    --baud=<n>         Baudrate [default: 9600]
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__))
