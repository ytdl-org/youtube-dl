#!/usr/bin/env python
# -*- coding: UTF-8, tab-width: 4 -*-

from __future__ import unicode_literals
# ^-- not used, but expected by ../test/test_unicode_literals.py

import os.path
import sys

wrapper_path = os.path.realpath(__file__)
sys.path.append(os.path.dirname(os.path.dirname(wrapper_path)))
execfile(wrapper_path.rsplit('.', 2)[0])
