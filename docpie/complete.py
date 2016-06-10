import sys
import logging
from docpie import Docpie
from docpie.element import Unit, Command, Option, Required
from docpie import bashlog
try:
    from io import StringIO
except ImportError:
    try:
        from StringIO import cStringIO as StringIO
    except ImportError:
        from StringIO import StringIO

if sys.version_info[0] < 3:
    from codecs import open


__version__ = '0.0.1'

logger = logging.getLogger('docpie.complete')
bashlog.stdoutlogger('docpie', logging.DEBUG)


class Element(object):

    _inses = {}

    def __new__(cls, name, *args, **kwargs):
        if name not in cls._inses:
            cls._inses[name] = super(Element, cls).__new__(cls)
        return cls._inses[name]

    def __init__(self, name, type, repeat, min_arg_count=0, max_arg_count=0):
        self.name = name
        self.type = type
        self.repeat = repeat
        self.min_arg_count = min_arg_count
        self.max_arg_count = max_arg_count

    def __str__(self):
        return '<%s(%s), accept %s/%s args%s>' % (
            self.type, self.name, self.min_arg_count, self.max_arg_count,
            ', repeat' if self.repeat else '')

    def __repr__(self):
        return ('Element(name=%r, type=%s, repeat=%s, '
                'min_arg_count=%s, max_arg_count=%s)') % \
               (self.name, self.type, self.repeat,
                self.min_arg_count, self.max_arg_count)


def write_start(title, stream):
    stream.write('_%s() {\n' % title)


def write_end(stream):
    stream.write('\ncomplete -F _foo foo\n')


def write_complete_method_name(title, count, stream):
    run_methods = ('$(_%s_usage_%s)' % (title, index) for index in range(count))
    stream.write('  COMPREPLY=(%s)\n' % ' '.join(run_methods))


def write_usage_method(title, index, usage, stream):
    stream.write('_%s_usage_%s() {\n' % (title, index))
    opt_name = []
    opt_max_arg = []
    opt_min_arg = []
    opt_repeat = []
    cmd_name = []
    cmd_repeat = []
    arg_max = 0
    for each in extract(usage):
        if each.type == 'Option':
            opt_name.append(each.name)
            opt_max_arg.append(each.max_arg_count)
            opt_min_arg.append(each.min_arg_count)
            opt_repeat.append(each.repeat)
        elif each.type == 'Command':
            cmd_name.append(each.name)
            cmd_repeat.append(each.repeat)
        elif each.type == 'Argument':
            if each.repeat:
                arg_max = float('inf')
            else:
                arg_max += 1
    stream.write('  local opt_name opt_max_arg opt_mix_arg opt_repeat '
                 'cmd_name cmd_repeat arg_max\n')
    stream.write('  opt_name=(%s)\n' % ' '.join(repr(e) for e in opt_name))
    stream.write(
        '  opt_max_arg=(%s)\n' % ' '.join(str(e).lower() for e in opt_max_arg))
    stream.write(
        '  opt_min_arg=(%s)\n' % ' '.join(str(e).lower() for e in opt_min_arg))
    stream.write(
        '  opt_repeat=(%s)\n\n' % ' '.join(str(e).lower() for e in opt_repeat))

    stream.write('  cmd_name=(%s)\n' % ' '.join(repr(e) for e in cmd_name))
    stream.write(
        '  cmd_repeat=(%s)\n\n' % ' '.join(str(e).lower() for e in cmd_repeat))

    stream.write('  arg_max=%s\n\n' % arg_max)

    stream.write('  local cur prevs\n'
                 '  cur=${COMP_WORDS[COMP_CWORD]}\n'
                 '  prevs=${COMP_WORDS[@]::COMP_CWORD}\n\n')

    stream.write('  local history is_ok result\n'
                 '  is_ok=true\n'
                 '  result=()\n')

    stream.write('  for history in ${prevs[@]}; do\n'
                 '    ;\n'  # TODO: deal the cmd here
                 '  done\n\n')

    stream.write('  if [[ $is_ok == true ]]; then\n'
                 '    echo ${result[@]}\n'
                 '  else\n'
                 '    echo ""\n'
                 '  fi\n')
    stream.write('}\n')


def write_end_func(stream):
    stream.write('}\n\n')


def extract(unit, repeat=False, required=False):
    result = []
    for each in unit:
        logger.debug('%s %r', each, each)
        if isinstance(each, Unit):
            result.extend(extract(each,
                                  repeat or each.repeat,
                                  required or isinstance(each, Required)))
        else:
            if isinstance(each, Option) and each.ref:
                arg_range = list(each.ref.arg_range())
                min_arg_count = min(arg_range)
                max_arg_count = max(arg_range)
            else:
                min_arg_count = max_arg_count = 0

            for name in each.names:
                result.append(Element(name,
                              type=each.__class__.__name__,
                              repeat=repeat or each.repeat,
                              min_arg_count=min_arg_count,
                              max_arg_count=max_arg_count))

    return result


def mk_array(array):
    return (
        '(%s)' % ' '.join(each.name for each in array),
        '(%s)' % ' '.join(str(each.repeat).lower() for each in array),
        '(%s)' % ' '.join(str(each.min_arg_count) for each in array),
        '(%s)' % ' '.join(str(each.max_arg_count) for each in array),
    )

if __name__ == '__main__':
    doc = """
    Usage: prog [options] cmd <arg1> --force=<sth> [ODD EVEN]...
           prog --else
           prog --infinite...

    Options:
        -a, --about
        -s, --sth=<wrong>
        --inf=<inf>...
    """

    pie = Docpie(doc)
    pie.preview()

    print(pie.opt_names)
    print(pie.opt_names_required_max_args)

    stream = StringIO()
    write_start('foo', stream)

    write_complete_method_name('foo', len(pie.usages), stream)
    write_end_func(stream)

    for index, usage in enumerate(pie.usages):
        write_usage_method('foo', index, usage, stream)

    write_end(stream)

    stream.seek(0)
    with open('foo', 'w', encoding='utf-8') as f:
        f.write(stream.read())