import unittest
import logging

from docpie.test.test_usage_parse import case as u_case
from docpie.test.test_element import case as e_case
from docpie.test.test_section import case as s_case
from docpie.test.test_match import case as t_case
from docpie.test.test_docpie import case as d_case
from docpie import bashlog

logger = logging.getLogger('docpie.test')


def suite():
    return unittest.TestSuite(case())


def case():
    lis = []
    for each_case in (u_case, e_case, s_case, t_case, d_case):
        lis.extend(each_case())
    return lis


def main():
    unittest.TextTestRunner().run(suite())

if __name__ == '__main__':
    # bashlog.getlogger('docpie', bashlog.WARNING, True)
    logging.getLogger().setLevel(logging.CRITICAL)
    main()
