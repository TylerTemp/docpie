import logging
import warnings
from docpie.element import Unit, Option, Required
try:
    from io import StringIO
except ImportError:
    try:
        from StringIO import cStringIO as StringIO
    except ImportError:
        from StringIO import StringIO


__version__ = '0.0.1'

logger = logging.getLogger('docpie.complete')


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


def write_header(title, stream):
    stream.write(('#!/usr/bin/env bash\n'
                  '# docpie autocomplete for bash, version %s\n'
                  '# author: TylerTemp <tylertempdev@gmail.com>\n\n') %
                 __version__)

def write_get_index(title, stream):
    stream.write((
        '_%s_get_index() {\n'
        '  local find_in index value i\n'
        '  index=-1\n'
        '  value=$1\n'
        '  shift\n'
        '  find_in=("$@")\n\n'

        '  for i in "${!find_in[@]}"; do\n'
        '    if [[ "${find_in[$i]}" = "${value}" ]]; then\n'
        '      index=$i\n'
        '      break\n'
        '    fi\n'
        '  done\n'
        '  echo "$i"\n'
        '}\n\n') % title)


def write_main(title, count, stream):
    stream.write('_%s() {\n' % title)
    run_methods = ('$(_%s_usage_%s)' % (title, index)
                   for index in range(count))
    stream.write('  COMPREPLY=(%s)\n' % ' '.join(run_methods))
    stream.write('}\n\n')


def write_end(title, stream):
    stream.write(
        '\n\ncomplete -o bashdefault -o default -o filenames -F _%s %s\n' %
        (title, title)
    )


def write_usage_method(title, index, usage, stream):
    stream.write('_%s_usage_%s() {\n' % (title, index))
    opt_name = []
    opt_arg = []
    opt_repeat = []
    cmd_name = []
    cmd_repeat = []
    arg_max = 0
    for each in extract(usage):
        if each.type == 'Option':
            opt_name.append(each.name)
            opt_min = each.min_arg_count
            if opt_min != each.max_arg_count:
                warnings.warn(
                    '%s accepts arguments of non-fixed length' % each)
            if opt_min == float('inf'):
                warnings.warn('%s accepts infinity number of arguments' % each)
                opt_min = 1000  # a little trick
            opt_arg.append(opt_min)
            opt_repeat.append(each.repeat)
        elif each.type == 'Command':
            cmd_name.append(each.name)
            cmd_repeat.append(each.repeat)
        elif each.type == 'Argument':
            if each.repeat:
                arg_max = float('inf')
            else:
                arg_max += 1
    stream.write('  local opt_name opt_arg opt_repeat cmd_name cmd_repeat '
                 'arg_max\n')
    stream.write('  opt_name=(%s)\n' % ' '.join(repr(e) for e in opt_name))
    stream.write('  opt_arg=(%s)\n' %
                 ' '.join(str(e).lower() for e in opt_arg))
    stream.write('  opt_repeat=(%s)\n\n' %
                 ' '.join(str(e).lower() for e in opt_repeat))

    stream.write('  cmd_name=(%s)\n' % ' '.join(repr(e) for e in cmd_name))
    stream.write('  cmd_repeat=(%s)\n\n' %
                 ' '.join(str(e).lower() for e in cmd_repeat))

    stream.write('  arg_max=%s\n\n' % arg_max)

    stream.write('  local cur prevs\n'
                 '  cur=${COMP_WORDS[COMP_CWORD]}\n'
                 '  prevs=(${COMP_WORDS[@]:1:COMP_CWORD})\n\n')

    stream.write('  local hist_index hist_count\n'
                 '  hist_index=0\n'
                 '  hist_count=$(expr $COMP_CWORD - 1)\n\n')

    # note even we use `--sth=else` in command line
    # the `COMP_WORDS` will be expanded as `--sth = else`
    # this is not considered in this script :(
    stream.write((
        '  while [[ $hist_index -lt $hist_count ]]; do\n'
        '    hist=${prevs[$hist_index]}\n\n'

        '    if [[ $hist = "--" && $COMP_CWORD -gt $hist_index ]]; then\n'
        '      compgen -o filenames -A file -- "$cur"\n'
        '      return\n'
        '    fi\n\n'

        '    case $hist in\n'
        '      --*)\n'
        '        next_elem=${prevs[$hist_index+1]}\n'
        '        if [[ $next_elem == "=" ]]; then\n'
        '          hist_index=$(expr $hist_index + 1)\n'
        '        fi\n\n'
        '        index=$(_%(title)s_get_index $hist ${opt_name[@]})\n'
        '        if [[ index == -1 ]]; then\n'
        '          echo ""\n'
        '          return\n'
        '        fi\n'
        '        arg_num=${opt_arg[$index]}\n'
        '        if [[ ($next_elem == "=") && ($arg_num -lt 1) ]]; then\n'
        '          echo ""\n'
        '          return\n'
        '        fi\n'
        '        hist_index=$(expr $hist_index + $arg_num + 1)\n\n'

        '        if [[ ${opt_repeat[$index]} == false ]]; then\n'
        '          opt_name=(${opt_name[@]::$index} ${opt_name[@]:$index+1})\n'
        '          opt_arg=(${opt_arg[@]::$index} ${opt_arg[@]:$index+1})\n'
        '          opt_repeat=(${opt_repeat[@]::$index} ${opt_repeat[@]:$index+1})\n'
        '        fi\n'
        '        ;;\n'
        '      -*)\n'
        '        index=$(_foo_get_index $hist ${opt_name[@]})\n'
        '        if [[ index != -1 ]]; then\n'
        '          hist_index=$(expr $hist_index + ${opt_arg[$index]} + 1)\n'
        '          if [[ ${opt_repeat[$index]} != true ]]; then\n'
        '            opt_name=(${opt_name[@]::$index} ${opt_name[@]:$index+1})\n'
        '            opt_arg=(${opt_arg[@]::$index} ${opt_arg[@]:$index+1})\n'
        '            opt_repeat=(${opt_repeat[@]::$index} ${opt_repeat[@]:$index+1})\n'
        '          fi\n'
        '        else\n'
        '          hist_index=$(expr $hist_index + 1)\n'
        '        fi\n'
        '        ;;\n'
        '      *)\n'
        '        index=$(_%(title)s_get_index $hist ${cmd_name[@]})\n'
        '        if [[ index != -1 ]]; then\n'
        '          if [[ ${cmd_repeat[$index]} != true ]]; then\n'
        '            cmd_name=(${cmd_name[@]::$index} ${cmd_name[@]:$index+1})\n'
        '            cmd_repeat=(${cmd_repeat[@]::$index} ${cmd_repeat[@]:$index+1})\n'
        '          fi\n'
        '        else\n'
        '          arg_max=$(expr $arg_max - 1)\n'
        '        fi\n'
        '        hist_index=$(expr $hist_index + 1)\n'
        '        ;;\n'
        '    esac\n'
        '  done\n\n'
    ) % {'title': title})

    stream.write(
        '  if [[ $hist_index -gt $hist_count ]]; then\n'
        '    compgen -o filenames -A file -- "$cur"\n'
        '    return\n'
        '  fi\n\n'

        '  if [[ $arg_max == inf || $arg_max -ge 0 ]]; then\n'
        '    result=($(compgen -W "${opt_name[*]} ${cmd_name[*]}" -- "$cur") $(compgen -o filenames -A file -- "$cur"))\n'
        '    echo "${result[@]}"\n'
        '  elif [[ $arg_max -eq 0 ]]; then\n'
        '    compgen -W "${opt_name[*]} ${cmd_name[*]}" -- "$cur"\n'
        '  else\n'
        '    compgen -o filenames -A file -- "$cur"\n'
        '  fi\n'
    )

    stream.write('}\n')


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


def bash(pie, title=None, stream=None):
    if stream is None:
        the_stream = StringIO()
    else:
        the_stream = stream
    if title is None:
        title = pie.name
    if title is None:
        raise ValueError('title value missed')

    write_header(title, the_stream)
    write_get_index(title, the_stream)
    write_main(title, len(pie.usages), the_stream)

    for index, usage in enumerate(pie.usages):
        write_usage_method(title, index, usage, the_stream)

    write_end(title, the_stream)

    if stream is None:
        the_stream.seek(0)
        return the_stream.read()


if __name__ == '__main__':
    from docpie import Docpie
    logging.getLogger('docpie').setLevel(logging.CRITICAL)
    doc = """
    Usage: prog [options] cmd <arg1> --force=<sth> [odd even]...
           prog --else
           prog --infinite...

    Options:
        -a, --about
        -s, --sth=<wrong>
        --inf=<inf>
    """

    pie = Docpie(doc)
    result = bash(pie, 'demo')
    print(result)
