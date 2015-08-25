import unittest
import logging
import sys
import json
import difflib
from pprint import pprint

from docpie.tracemore import get_exc_plus
from docpie import docpie, Docpie
from docpie import bashlog
from docpie.parser import UsageParser, OptionParser, Parser
from docpie.element import *
from docpie.tokens import Argv
from docpie.saver import Saver
from docpie.error import DocpieExit

bashlog.stdoutlogger(logger=None, level=bashlog.DEBUG, color=True)


# doc = '''usage: prog (go <direction> --speed=<km/h>)...
doc = '''Usage: prog [options]

Options: -p PATH, --path=<path>  Path to files.
'''

sys.argv = ['prog', '-proot']

# # basic usage
#
# match_dict = docpie.docpie(doc, sys.argv)
#
# # save
#
docpie = Docpie(doc)
#
# # dump json
#

old_dict = docpie.convert_2_dict()
result = json.dumps(old_dict)
#
# # load json
#
# pprint(docpie.convert_2_dict())

ins = Docpie.convert_2_docpie(json.loads(result))


new_dict = ins.convert_2_dict()

# docpie = Docpie.convert_2_docpie(json.loads(result))
#
# # dump pickle
#
# result = pickle.dumps(docpie)
#
# # load pickle
#
# docpie = pickle.loads(result)
#
# # use from class
#
# docpie = Docpie(doc)
# matched_dict = docpie.docpie(sys.argv)


# ins = Required(Option('--speed', ref=Required(Argument('<km/h>'))),
#                repeat=True)
# token = Argv(['--speed=5', '--speed=9'])
# ins.match(token, Saver(), False)
# print(ins.get_value())


# docpie_obj = Docpie(doc)
# usage_list = UsageParser(docpie_obj.usage_text).get_chain()
# option_list = OptionParser(docpie_obj.option_text).get_chain()
#
# print(usage_list)

# opts, usages = Parser.fix(option_list, usage_list)
# print(usages[-1][-1][-1])

# for opt in opts:
#     print(opt)

# doc = '''prog -b cmd1 -a cmd2 -b'''
#
# p = UsageParser(doc)
# c = p.get_chain()[0]
# saver = Saver()
# argv = Argv('-b -a cmd1 cmd2 -b'.split())
# try:
#     print(c.match(argv, saver, False))
# except BaseException as e:
#     err = get_exc_plus()
#     print(err)
#     sys.exit(1)
#
# print(argv)
#
# print('-' * 45)
#
# doc = '''prog -b cmd1 -a cmd2 -b'''
#
# p = UsageParser(doc)
# c = p.get_chain()[0]
# saver = Saver()
# argv = Argv('-b -a cmd2 cmd1 -b'.split())
#
# print(c.match(argv, saver, False))
# print('should fail')
#
# print(argv)
#
# print('-' * 45)
#
# doc = '''prog -b (cmd1 -a) cmd2 -b'''
#
# p = UsageParser(doc)
# c = p.get_chain()[0]
# saver = Saver()
# argv = Argv('-b -b cmd1 cmd2 -a'.split())
#
# print(c.match(argv, saver, False))
#
# print(argv)
