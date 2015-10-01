'''
usage: python git.py branch [options]
                            [-r | -a] [--merged=<commit> | --no-merged=<commit>]
       python git.py branch [options] [-l] [-f] <branchname> [<start-point>]
       python git.py branch [options] [-r] (-d | -D) <branchname>
       python git.py branch [options] (-m | -M) [<oldbranch>] <newbranch>

options:
    -h, --help
    -v, --verbose         show hash and subject, give twice for upstream branch
    -t, --track           set up tracking mode (see git-pull(1))
    --set-upstream        change upstream info
    --color=<when>        use colored output
    -r                    act on remote-tracking branches
    --contains=<commit>   print only branches that contain the commit
    --abbrev=<n>          use <n> digits to display SHA-1s
    -a                    list both remote-tracking and local branches
    -d                    delete fully merged branch
    -D                    delete branch (even if not merged)
    -m                    move/rename a branch and its reflog
    -M                    move/rename a branch, even if target exists
    -l                    create the branch's reflog
    -f, --force           force creation (when already exists)
    --no-merged=<commit>  print only not merged branches
    --merged=<commit>     print only merged branches
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__, name='git.py'))
