from __future__ import unicode_literals, print_function

from inspect import getsource
import os
from os.path import dirname as dirn
import sys

print('WARNING: Lazy loading extractors is an experimental feature that may not always work', file=sys.stderr)

sys.path.insert(0, dirn(dirn((os.path.abspath(__file__)))))

lazy_extractors_filename = sys.argv[1]
if os.path.exists(lazy_extractors_filename):
    os.remove(lazy_extractors_filename)

from youtube_dl.extractor import _ALL_CLASSES
from youtube_dl.extractor.common import InfoExtractor

with open('devscripts/lazy_load_template.py', 'rt') as f:
    module_template = f.read()

module_contents = [module_template + '\n' + getsource(InfoExtractor.suitable)]

ie_template = '''
class {name}(LazyLoadExtractor):
    _VALID_URL = {valid_url!r}
    _module = '{module}'
'''

make_valid_template = '''
    @classmethod
    def _make_valid_url(cls):
        return {valid_url!r}
'''


def build_lazy_ie(ie, name):
    valid_url = getattr(ie, '_VALID_URL', None)
    s = ie_template.format(
        name=name,
        valid_url=valid_url,
        module=ie.__module__)
    if ie.suitable.__func__ is not InfoExtractor.suitable.__func__:
        s += '\n' + getsource(ie.suitable)
    if hasattr(ie, '_make_valid_url'):
        # search extractors
        s += make_valid_template.format(valid_url=ie._make_valid_url())
    return s

names = []
for ie in list(sorted(_ALL_CLASSES[:-1], key=lambda cls: cls.ie_key())) + _ALL_CLASSES[-1:]:
    name = ie.ie_key() + 'IE'
    src = build_lazy_ie(ie, name)
    module_contents.append(src)
    names.append(name)

module_contents.append(
    '_ALL_CLASSES = [{0}]'.format(', '.join(names)))

module_src = '\n'.join(module_contents) + '\n'

with open(lazy_extractors_filename, 'wt') as f:
    f.write(module_src)
