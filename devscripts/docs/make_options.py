from __future__ import unicode_literals
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import youtube_dl
from youtube_dl.utils import compat_str

OPTONS_FILE = 'docs/options.rst.inc'
parser,_ ,_ = youtube_dl.parseOpts()

with io.open(OPTONS_FILE, 'wt', encoding='utf-8') as f:
    f.write('.. program:: youtube-dl\n\n')
    for group in parser.option_groups:
        title = compat_str(group.title)
        f.write(title + '\n')
        f.write('-' * len(title) + '\n')
        for option in group.option_list:
            f.write('.. option:: ')
            f.write(compat_str(option).replace('/', ', '))
            if option.metavar:
                f.write(' <%s>' % option.metavar)
            f.write('\n\n')
            f.write(' ' * 4 + option.help)
            f.write('\n\n')
        f.write('\n')

