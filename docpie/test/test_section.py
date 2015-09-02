import unittest

from docpie import Docpie
from docpie.parser import Parser, OptionParser


class DocpieTest(unittest.TestCase):
    def eq(self, doc, expected):
        result, _ = Parser.parse_section(doc, "Usage:")
        self.assertEqual(result, expected)

    def test_singleline(self):
        doc = '''Usage: test'''
        self.eq(doc, '       test')

    def test_oneline_mulit(self):
        doc = '''
        Usage: line1
               line2
               line3
               line4

           not'''
        expect = '''\
               line1
               line2
               line3
               line4'''

        self.eq(doc, expect)

    def test_multiline(self):
        doc = '''
        Usage:
            test
            line

        '''
        expect = '''\
            test
            line'''
        self.eq(doc, expect)

    def test_multi(self):
        doc = '''Usage:
        line
        line
        line

        not'''
        expect = '''\
        line
        line
        line'''
        self.eq(doc, expect)


class OptionParserTest(unittest.TestCase):

    def eq(self, doc, expected):
        self.assertEqual(
            OptionParser(doc, True)._opt_and_default_str, expected)

    def test_default(self):
        doc = '''\
        -f --file  nothing
        -v --verbose\tstill nothing
        -m,--multi=<test>
           Yes, default goes
           here. [default:  ]
        -pmsg, --print <msg>     still default[default: yes]
        -a --all=<list>  here
                         we are
                         [default: ,]'''
        self.eq(doc, [
                        ('-f --file', None),
                        ('-v --verbose', None),
                        ('-m,--multi=<test>', ' '),
                        ('-pmsg, --print <msg>', 'yes'),
                        ('-a --all=<list>', ','),
                     ])

    def test_unstandard_arg(self):
        doc = '''\
        -t, --tab=<\tformat>\t\\t in bracket[default: \t]
        -s, --space=<    >  spaces in bracket[default:  ]'''
        self.eq(doc, [
                        ('-t, --tab=<\tformat>', '\t'),
                        ('-s, --space=<    >', ' '),
                     ]
                )


def suite():
    return unittest.TestSuite(case())


def case():
    return (
            unittest.TestLoader().loadTestsFromTestCase(DocpieTest),
            unittest.TestLoader().loadTestsFromTestCase(OptionParserTest),
        )

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
