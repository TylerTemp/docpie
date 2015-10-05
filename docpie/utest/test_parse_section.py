import unittest
import logging
from docpie.parser import OptionParser, UsageParser
logger = logging.getLogger('docpie.test.parse_section')


class OptionsTest(unittest.TestCase):

    def p(self, text, name='Options:', case_sensitive=False):
        return OptionParser.parse(text, name, case_sensitive)

    def test_parse(self):
        doc = '''
        Not Part

            Options:
                -a
                -b
                -c

            Global Options:
                -d
                -e
                -f

            Command Options:
                -g
                -h


            Inline Options: -i
                            -j



            Inline2 Options:   -k
                               -l
            Nearer Options: -m
                             -n

        Not Part'''
        fmted, dic = self.p(doc)
        # print(fmted)
        # for k, v in dic.items():
        #     print('%10r: %r' % (k, v))
        self.assertEqual(
            fmted,
            '-a\n-b\n-c\n-d\n-e\n-f\n-g\n-h\n-i\n-j\n-k\n-l\n-m\n -n')
        self.assertEqual(
            dic,
            {'': ('            Options:\n'
                  '                -a\n'
                  '                -b\n'
                  '                -c'),
             'Global': ('            Global Options:\n'
                        '                -d\n'
                        '                -e\n'
                        '                -f'),
             'Inline2': ('            Inline2 Options:   -k\n'
                         '                               -l'),
             'Command': ('            Command Options:\n'
                         '                -g\n'
                         '                -h'),
             'Nearer': ('            Nearer Options: -m\n'
                        '                             -n'),
             'Inline': ('            Inline Options: -i\n'
                        '                            -j')})

class UsageTest(unittest.TestCase):

    def p(self, text, name='Usage:', case_sensitive=False):
        return UsageParser.parse(text, name, case_sensitive)

    def test_parse(self):
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

        expect2 = '''\
        Usage: line1
               line2
               line3
               line4'''

        result = self.p(doc)
        self.assertEqual(result[0], expect)
        self.assertEqual(result[1], expect2)

if __name__ == '__main__':
    # from docpie.bashlog import stdoutlogger, DEBUG
    # stdoutlogger(None, DEBUG)
    unittest.main()
    # OptionsTest().test_parse()
    # UsageTest().test_parse()