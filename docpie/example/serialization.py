"""
Usage:
    serialization dump [options] [--path=<path>]
    serialization load [options] [preview] [--path=<path>]
    serialization clear
    serialization preview

Options:
    -p, --path=<path>           save or load path or filename[default: ./]
    -f, --format=<format>...    save format, "json" or "pickle"
                                [default: json pickle]
    -n, --name=<name>           save or dump filename without extension,
                                default is the same as this file
    -h, -?                      print usage
    --help                      print this message
    -v, --version               print the version
"""

import sys
import os
import json
try:
    import cPickle as pickle
except ImportError:    # py3 maybe
    import pickle
from docpie import Docpie, __version__


def short_help_handler(pie, flag):
    print(pie.usage_text)
    print('')
    print('Use `--help` to see more help message')
    sys.exit()

pie = Docpie(__doc__, version=__version__)
pie.set_auto_handler('-?', short_help_handler)

result = pie.docpie()
print(pie)

if result['dump']:
    path = result['--path']
    assert os.path.isdir(path)
    name = result['--name']
    if name is None:
        name, _ = os.path.splitext(__file__)
        _, name = os.path.split(name)
    file = os.path.join(path, name)
    fmt = result['--format']

    if 'json' in fmt:
        full_file = file + '.json'
        with open(full_file, 'w', encoding='utf-8') as f:
            json.dump(pie.convert_2_dict(), f, indent=2)
        print('save json in %s' % full_file)

    if 'pickle' in fmt:
        full_file = file + '.pickle'
        with open(full_file, 'wb') as f:
            pickle.dump(pie, f)
        print('save pickle in %s' % full_file)

    if result['preview']:
        pie.preview()

    sys.exit()

if result['load']:
    path = result['--path']
    assert os.path.isdir(path)
    name = result['--name']
    if name is None:
        name, _ = os.path.splitext(__file__)
        _, name = os.path.split(name)
    file = os.path.join(path, name)
    fmt = result['--format']
    pies = {}

    if 'json' in fmt:
        full_file = file + '.json'
        with open(full_file, 'r', encoding='utf-8') as f:
            pie = Docpie.convert_2_docpie(json.load(f))
        pie.set_auto_handler('-?', short_help_handler)
        pies['json'] = pie
        print('load json from %s' % full_file)

    if 'pickle' in fmt:
        full_file = file + '.pickle'
        with open(full_file, 'rb') as f:
            pie = pickle.load(f)
        pies['pickle'] = pie
        print('load pickle from %s' % full_file)

    if result['preview']:
        for k, pie in pies.items():
            print('\n[<<<%s>>>]\n' %
                  ('<<< Docpie from %s >>>' % k).center(72, '='))
            pie.preview()

    sys.exit()

if result['preview']:
    pie.preview()
    sys.exit()

if result['clear']:
    path = result['--path']
    assert os.path.isdir(path)
    name = result['--name']
    if name is None:
        name, _ = os.path.splitext(__file__)
        _, name = os.path.split(name)
    file = os.path.join(path, name)
    for each in (file + '.json', file + '.pickle'):
        if os.path.isfile(each):
            os.unlink(each)
            print('%s removed' % each)
