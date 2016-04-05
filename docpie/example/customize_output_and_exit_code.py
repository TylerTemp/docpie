"""
This is a example to fully customize any output of ``docpie``

Usage:
    prog [options] my [--family | --given] name is <your name>
    prog [options] my --family-name=<name>
    prog [options] my --given-name=<name>

Options:
    -v, --version
    -h, -?, --help
Hidden Options:
    --debug
"""
import sys
from docpie import docpie, \
                   DocpieExit, \
                   UnknownOptionExit, ExceptNoArgumentExit, \
                   ExpectArgumentExit, \
                   ExpectArgumentHitDoubleDashesExit, \
                   AmbiguousPrefixExit, \
                   __version__


def version_handler(pie, flag):
    print("version %s? That's a brand new release!" % pie.version)
    print("Hey you just pass %r to me" % flag)
    sys.exit()


def help_handler(pie, flag):
    print("Ok here is the help. But try to put some wrong command, "
          "to see how the customization is done.\n")
    if flag.startswith('--'):
        print(pie.doc)

        print(
            '\n'
            'Try the following command:\n'
            '  my --sur name is "Slim Shady"\n'
            '  my --fami is Shady\n'
            '  my --given=name is Shady\n'
            '  my --given-name -- Slim\n'
            '  my name is Slim Shady\n'
            '  my name is "Slim Shady"\n'
        )
    else:
        print(pie.usage_text)
        for title, content in pie.option_sections.items():
            if title.lower() == 'hidden':
                continue
            print(content)

        print('\nActually one option section is hidden. Try `--help` to see it')
    sys.exit()


try:
    args = docpie(__doc__, version=__version__, extra={
        ('-h', '--help', '-?'): help_handler,
        ('-v', '--version'): version_handler,
    })
except UnknownOptionExit as e:
    sys.stderr.write('What do you mean by %r?\n' % e.option)
    sys.exit(1)
except ExceptNoArgumentExit as e:
    sys.stderr.write(('"%s" can not follows "%s".\n'
                      "Do you mean `my --%s name is ...`?\n") %
                     (e.hit, '/'.join(e.option),
                      '/'.join(e.option).split('-')[2]))
    sys.exit(2)
except ExpectArgumentHitDoubleDashesExit as e:
    sys.stderr.write(
        'NO, no. put your name directly after %s, not "--"\n' %
        '/'.join(e.option)
    )
    sys.exit(3)
except ExpectArgumentExit as e:
    sys.stderr.write(
        'put your name after %s, for real man.\n' %
        '/'.join(e.option)
    )
    sys.exit(4)
except AmbiguousPrefixExit as e:
    sys.stderr.write(
        'When you said %s, you mean %s?\n' %
        (e.prefix, ' or '.join(e.ambiguous))
    )
    sys.exit(5)
except DocpieExit as e:
    sys.stderr.write('Alright you got me. Something went wrong with your '
                     'input %s\n\n' %
                     ((': %s' %e.msg) if e.msg else "but I don't know what."))
    sys.stderr.write(e.usage_text)
    sys.stderr.write('\n')
    for title, content in e.option_sections.items():
        if title.lower() == 'hidden':
            continue
        sys.stderr.write(content)
        sys.stderr.write('\n')
    sys.stderr.write('\nUse `--help` to see more\n')
    sys.exit(6)
else:
    is_fname = args['--family'] or (args['--family-name'] is not None)
    name = args['<your name>'] or args['--family-name'] or args['--given-name']

    pref = 'Mr./Ms. ' if is_fname else ''
    print('Hey, %s%s' % (pref, name))
