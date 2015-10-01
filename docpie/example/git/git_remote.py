'''
usage: python git.py remote [-v | --verbose]
       python git.py remote add [-t <branch>] [-m <master>] [-f] [--mirror] <name> <url>
       python git.py remote rename <old> <new>
       python git.py remote rm <name>
       python git.py remote set-head <name> (-a | -d | <branch>)
       python git.py remote [-v | --verbose] show [-n] <name>
       python git.py remote prune [-n | --dry-run] <name>
       python git.py remote [-v | --verbose] update [-p | --prune] [(<group> | <remote>)...]
       python git.py remote set-branches <name> [--add] <branch>...
       python git.py remote set-url <name> <newurl> [<oldurl>]
       python git.py remote set-url --add <name> <newurl>
       python git.py remote set-url --delete <name> <url>

options:
    -v, --verbose         be verbose; must be placed before a subcommand
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__, name='git.py'))
