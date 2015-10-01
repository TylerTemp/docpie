'''
Usage:
  quick_example.py tcp <host> <port> [--timeout=<seconds>]
  quick_example.py serial <port> [--baud=9600] [--timeout=<seconds>]
  quick_example.py -h | --help | --version
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__, version='0.0.1'))
