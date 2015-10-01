'''
Example of program which uses [options] shortcut in pattern.

Usage:
  options_shortcut_example.py [options] <port>

Options:
  -h --help                show this help message and exit
  --version                show version and exit
  -n, --number N           use N as a number
  -t, --timeout TIMEOUT    set timeout TIMEOUT seconds
  --apply                  apply changes to database
  -q                       operate in quiet mode
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__, version='0.0.1'))
