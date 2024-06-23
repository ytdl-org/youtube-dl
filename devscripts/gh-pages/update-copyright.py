#!/usr/bin/env python
# coding: utf-8

from __future__ import with_statement, unicode_literals

import datetime
import glob
import os
import re
import sys

dirn = os.path.dirname

sys.path.insert(0, dirn(dirn(dirn(os.path.abspath(__file__)))))

from devscripts.utils import read_file, write_file
from youtube_dl import compat_str

year = compat_str(datetime.datetime.now().year)
for fn in glob.glob('*.html*'):
    content = read_file(fn)
    newc = re.sub(r'(?P<copyright>Copyright © 2011-)(?P<year>\d{4})', 'Copyright © 2011-' + year, content)
    if content != newc:
        tmpFn = fn + '.part'
        write_file(tmpFn, newc)
        os.rename(tmpFn, fn)
