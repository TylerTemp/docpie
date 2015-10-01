'''
usage:
    python git.py [--version] [--exec-path=<path>] [--html-path]
                  [-p|--paginate|--no-pager] [--no-replace-objects]
                  [--bare] [--git-dir=<path>] [--work-tree=<path>]
                  [-c <name>=<value>] [--help]
                  <command> [<args>...]

options:
   -c <name=value>
   -h, --help
   -p, --paginate

The most commonly used git commands are:
   add        Add file contents to the index
   branch     List, create, or delete branches
   checkout   Checkout a branch or paths to the working tree
   clone      Clone a repository into a new directory
   commit     Record changes to the repository
   push       Update remote refs along with associated objects
   remote     Manage set of tracked repositories
See 'git help <command>' for more information on a specific command.
'''

from subprocess import call
from docpie import docpie
import sys
import os

if __name__ == '__main__':

    top_dir = os.path.abspath(os.path.dirname(__file__))

    args = docpie(__doc__, name='git.py',
                  version='git version 1.7.4.4', optionsfirst=True)

    print('global arguments:')
    print(args)
    print('command arguments:')

    argv = [args['<command>']] + args['<args>']
    print('argv: %s' % argv)
    if args['<command>'] == 'add':
        # In case subcommand is implemented as python module:
        sys.path.insert(0, top_dir)
        import git_add
        sys.path.pop(0)
        argv.insert(0, sys.argv[0])
        print(docpie(git_add.__doc__, name='git.py', argv=argv))
        sys.exit()

    elif args['<command>'] == 'branch':
        # In case subcommand is a script in some other programming language:
        sys.exit(
            call(['python', os.path.join(top_dir, 'git_branch.py')] + argv))

    elif args['<command>'] in 'checkout clone commit push remote'.split():
        # For the rest we'll just keep DRY:
        sys.exit(
            call(
                ['python',
                 os.path.join(top_dir, 'git_%s.py' % args['<command>'])
                ] + argv))

    elif args['<command>'] == 'help':
        sys.exit(
            call(['python', os.path.join(top_dir, 'git.py'), '--help']))

    else:
        sys.exit(
            "%r is not a git.py command. See 'git help'." % args['<command>'])
