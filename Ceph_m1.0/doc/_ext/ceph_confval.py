import io
from typing import Any, Dict, List, Union

from docutils.parsers.rst import directives
from docutils.parsers.rst import Directive

from sphinx.domains.python import PyField
from sphinx.locale import _
from sphinx.util import logging, status_iterator
from sphinx.util.docfields import Field

import jinja2
import jinja2.filters
import yaml


logger = logging.getLogger(__name__)


TEMPLATE = '''
.. confval_option:: {{ opt.name }}
{% if desc | length > 1 %}
   {{ desc | wordwrap(70) | indent(3) }}
{% endif %}
   :type: ``{{opt.type}}``
{%- if default %}
  {%- if opt.type == 'size' %}
   :default: ``{{ default | eval_size | iec_size }}``
  {%- elif opt.type == 'secs' %}
   :default: ``{{ default | readable_duration(opt.type) }}``
  {%- elif opt.type in ('uint', 'int', 'float') %}
   :default: ``{{ default | readable_num(opt.type) }}``
  {%- elif opt.type == 'millisecs' %}
   :default: ``{{ default }}`` milliseconds
  {%- elif opt.type == 'bool' %}
   :default: ``{{ default | string | lower }}``
  {%- else %}
   :default: ``{{ default }}``
  {%- endif -%}
{%- endif %}
{%- if opt.enum_values %}
   :valid choices:{% for enum_value in opt.enum_values -%}
{{" -" | indent(18, not loop.first) }} {{ enum_value | literal }}
{% endfor %}
{%- endif %}
{%- if opt.min is defined and opt.max is defined %}
   :allowed range: ``[{{ opt.min }}, {{ opt.max }}]``
{%- elif opt.min is defined %}
   :min: ``{{ opt.min }}``
{%- elif opt.max is defined %}
   :max: ``{{ opt.max }}``
{%- endif %}
{%- if opt.see_also %}
   :see also: {{ opt.see_also | map('ref_confval') | join(', ') }}
{%- endif %}
{% if opt.note %}
   .. note::
      {{ opt.note }}
{%- endif -%}
{%- if opt.warning %}
   .. warning::
      {{ opt.warning }}
{%- endif %}
'''


def eval_size(value) -> int:
    try:
        return int(value)
    except ValueError:
        times = dict(_K=1 << 10,
                     _M=1 << 20,
                     _G=1 << 30,
                     _T=1 << 40)
        for unit, m in times.items():
            if value.endswith(unit):
                return int(value[:-len(unit)]) * m
        raise ValueError(f'unknown value: {value}')


def readable_duration(value: str, typ: str) -> str:
    try:
        if typ == 'sec':
            v = int(value)
            postfix = 'second' if v == 1 else 'seconds'
            return f'{v} {postfix}'
        elif typ == 'float':
            return str(float(value))
        else:
            return str(int(value))
    except ValueError:
        times = dict(_min=['minute', 'minutes'],
                     _hr=['hour', 'hours'],
                     _day=['day', 'days'])
        for unit, readables in times.items():
            if value.endswith(unit):
                v = int(value[:-len(unit)])
                postfix = readables[0 if v == 1 else 1]
                return f'{v} {postfix}'
        raise ValueError(f'unknown value: {value}')


def do_plain_num(value: str, typ: str) -> str:
    if typ == 'float':
        return str(float(value))
    else:
        return str(int(value))


def iec_size(value: int) -> str:
    units = dict(Ei=60,
                 Pi=50,
                 Ti=40,
                 Gi=30,
                 Mi=20,
                 Ki=10,
                 B=0)
    for unit, bits in units.items():
        m = 1 << bits
        if value % m == 0:
            value //= m
            return f'{value}{unit}'
    raise Exception(f'iec_size() failed to convert {value}')


def do_fileize_num(value: str, typ: str) -> str:
    v = eval_size(value)
    return iec_size(v)


def readable_num(value: str, typ: str) -> str:
    e = ValueError()
    for eval_func in [do_plain_num,
                      readable_duration,
                      do_fileize_num]:
        try:
            return eval_func(value, typ)
        except ValueError as ex:
            e = ex
    raise e


def literal(name) -> str:
    if name:
        return f'``{name}``'
    else:
        return f'<empty string>'


def ref_confval(name) -> str:
    return f':confval:`{name}`'


def jinja_template() -> jinja2.Template:
    env = jinja2.Environment()
    env.filters['eval_size'] = eval_size
    env.filters['iec_size'] = iec_size
    env.filters['readable_duration'] = readable_duration
    env.filters['readable_num'] = readable_num
    env.filters['literal'] = literal
    env.filters['ref_confval'] = ref_confval
    return env.from_string(TEMPLATE)


FieldValueT = Union[bool, float, int, str]


class CephOption(Directive):
    """
    emit option loaded from given command/options/<name>.yaml.in file
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {'default': directives.unchanged}

    template = jinja_template()
    opts: Dict[str, Dict[str, FieldValueT]] = {}

    def _load_yaml(self) -> Dict[str, Dict[str, FieldValueT]]:
        if CephOption.opts:
            return CephOption.opts
        env = self.state.document.settings.env
        opts = []
        for fn in status_iterator(env.config.ceph_confval_imports,
                                  'loading options...', 'red',
                                  len(env.config.ceph_confval_imports),
                                  env.app.verbosity):
            env.note_dependency(fn)
            try:
                with open(fn, 'r') as f:
                    yaml_in = io.StringIO()
                    for line in f:
                        if '@' not in line:
                            yaml_in.write(line)
                    yaml_in.seek(0)
                    opts += yaml.safe_load(yaml_in)['options']
            except OSError as e:
                message = f'Unable to open option file "{fn}": {e}'
                raise self.error(message)
        CephOption.opts = dict((opt['name'], opt) for opt in opts)
        return CephOption.opts

    def run(self) -> List[Any]:
        name = self.arguments[0]
        opt = self._load_yaml().get(name)
        if opt is None:
            raise self.error(f'Option "{name}" not found!')
        desc = opt.get('fmt_desc') or opt.get('long_desc') or opt.get('desc')
        opt_default = opt.get('default')
        default = self.options.get('default', opt_default)
        rendered = self.template.render(opt=opt, desc=desc, default=default)
        lineno = self.lineno - self.state_machine.input_offset - 1
        source = self.state_machine.input_lines.source(lineno)
        self.state_machine.insert_input(rendered.split('\n'), source)
        return []


def setup(app) -> Dict[str, Any]:
    app.add_config_value('ceph_confval_imports',
                         default=[],
                         rebuild='html',
                         types=[str])
    app.add_directive('confval', CephOption)
    app.add_object_type(
        'confval_option',
        'confval',
        objname='configuration value',
        indextemplate='pair: %s; configuration value',
        doc_field_types=[
            PyField(
                'type',
                label=_('Type'),
                has_arg=False,
                names=('type',),
                bodyrolename='class'
            ),
            Field(
                'default',
                label=_('Default'),
                has_arg=False,
                names=('default',),
            ),
            Field(
                'required',
                label=_('Required'),
                has_arg=False,
                names=('required',),
            ),
            Field(
                'example',
                label=_('Example'),
                has_arg=False,
            )
        ]
    )
    app.add_object_type(
        'confsec',
        'confsec',
        objname='configuration section',
        indextemplate='pair: %s; configuration section',
        doc_field_types=[
            Field(
                'example',
                label=_('Example'),
                has_arg=False,
            )]
    )

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
