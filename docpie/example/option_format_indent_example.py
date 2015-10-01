'''
Usage: option_format_indent_example.py [options]

Options:
 -a, --all=<here>
     --you can write discription like this even starting
     with `--`, as long as you ensure it indent more
     (at least 2 more space) spaces.
 -b, --brillant=<there>  You can alse write  a long long long long
                         long long long long description at the same
                         line. But all the following line should have
                         the same indent.
 -c, --clever=<where>
    docopt have more strict `default` syntax. It must startswith
    `[default: `(note the space after colon), following your default
    value, and endswith `]`. The following default will be an empty
    string.[default: ]
 -d, --default=<strict>
    And this default will be a space. [default:  ]
 -e, --escape=[<space>]  Though it's not standrad POSIX, docpie support
                         flag that expecting uncertain numbers of args.
                         This default will not work because it
                         endswith a dot, and the defualt value (because
                         of `[<space>]`) will be `None` instead of
                         `False`[default: not-work].
 -t, --thanks=<my-friend>...
    when an option accept multiple values, the default will be
    seperated by white space(space, tab, ect.)[default: Calvary Brey]
'''

from docpie import docpie

if __name__ == '__main__':
    print(docpie(__doc__))
