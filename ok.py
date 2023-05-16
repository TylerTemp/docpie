"""Example for docpie, linux cp-like command


NAME
     cp -- copy files

USAGE:
     cp <source_file> ... <target_directory>
"""

from docpie import Docpie, logger, bashlog
import logging

# logger.setLevel(logging.DEBUG)
bashlog.getlogger(logger, logging.DEBUG)

argv = ['prog', 'source', 'target']
pie = Docpie(__doc__, argv)
# pie.preview()
pie.docpie(argv)
