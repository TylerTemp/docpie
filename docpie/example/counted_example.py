'''
Usage: counted_example.py --help
       counted_example.py -v...
       counted_example.py go [go]
       counted_example.py (--path=<path>)...
       counted_example.py <file> <file>

Try: counted_example.py -vvvvvvvvvv
     counted_example.py go go
     counted_example.py --path ./here --path ./there
     counted_example.py this.txt that.txt
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__))
