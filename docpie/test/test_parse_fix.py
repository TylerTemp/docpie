import unittest
import logging

from docpie import bashlog
from docpie.parser import UsageParser, OptionParser, Parser
from docpie.element import Atom, Argument, Command, Option, Optional, Required


class ParseFixTest(unittest.TestCase):

    def eq(self, usage_txt, options_txt, usage, options):
        usage_chain = UsageParser(usage_txt).get_chain()
        option_chain = OptionParser(options_txt).get_chain()
        fixusage, fixoption = Parser.fix(option_chain, usage_chain)
        self.assertEqual(fixusage, usage)
        self.assertEqual(fixoption, options)

    def test(self):
        opt_a = Option('-a')
        ref = Required(Required(Argument('<>'), repeat=True), Argument('<>'))
        opt_a.ref = ref
        self.eq('app -a <here>... <around>', '-a <go>... <go>    description',
                [opt_a],
                [Required(opt_a)])


def suite():
    return unittest.TestSuite(case())


def case():
    return (
            unittest.TestLoader().loadTestsFromTestCase(ParseFixTest),
        )

if __name__ == '__main__':
    bashlog.getlogger('docpie', bashlog.DEBUG, True)
    unittest.TextTestRunner().run(suite())
