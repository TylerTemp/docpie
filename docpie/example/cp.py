"""
Example for docpie, linux cp-like command


NAME
     cp -- copy files

USAGE:
     cp [options] <source_file> ... <target_directory>

OPTIONS:
     -f    If the destination file cannot be opened, remove it and create a
           new file, without prompting for confirmation regardless of its per-
           missions.
     -v, --verbose
           Cause cp to be verbose, showing files as they are copied.
     -X    Do not copy Extended Attributes (EAs) or resource forks.
     -R    If source_file designates a directory, cp copies the directory and
           the entire subtree connected at that point.
"""

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__))
