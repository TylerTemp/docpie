import unittest
import logging

from docpie.test.test_usage_parse import UsageParserTest
from docpie.test.test_element import TokenTest
from docpie.test.test_section import DocpieTest, OptionParserTest
from docpie.test.test_match import MatchTest
from docpie.test.test_docpie import DocpieBasicTest, DocpieRunDefaultTest
from docpie.test.test_parse_fix import ParseFixTest
from docpie import bashlog

logger = logging.getLogger('docpie.test')
all_test = (UsageParserTest,
            TokenTest,
            DocpieTest, OptionParserTest,
            MatchTest,
            DocpieBasicTest, DocpieRunDefaultTest,
            ParseFixTest)


def suite():
    return unittest.TestSuite(case())


def case():
    return [unittest.TestLoader().loadTestsFromTestCase(each)
            for each in all_test]


def main():
    unittest.TextTestRunner().run(suite())

if __name__ == '__main__':
    # bashlog.getlogger('docpie', bashlog.WARNING, True)
    logging.getLogger().setLevel(logging.CRITICAL)
    main()
