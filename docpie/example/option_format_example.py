'''
Usage: option_format_example.py [options]

Options: -h, -?, --help        print this screen
         --verbose             print more message
         -a --arg=<arg>        this flag accept argument
         -b <arg>, --br=<arg>  you can announce argument twice
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__))
