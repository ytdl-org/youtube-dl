#!/usr/bin/env python

"""
This script employs a VERY basic heuristic ('porn' in webpage.lower()) to check
if we are not 'age_limit' tagging some porn site
"""

# Allow direct execution
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import get_testcases
from youtube_dl.utils import compat_urllib_request

for test in get_testcases():
    try:
        webpage = compat_urllib_request.urlopen(test['url'], timeout=10).read()
    except:
        print('\nFail: {0}'.format(test['name']))
        continue

    webpage = webpage.decode('utf8', 'replace')

    if 'porn' in webpage.lower() and ('info_dict' not in test
                                      or 'age_limit' not in test['info_dict']
                                      or test['info_dict']['age_limit'] != 18):
        print('\nPotential missing age_limit check: {0}'.format(test['name']))

    elif 'porn' not in webpage.lower() and ('info_dict' in test and
                                            'age_limit' in test['info_dict'] and
                                            test['info_dict']['age_limit'] == 18):
        print('\nPotential false negative: {0}'.format(test['name']))

    else:
        sys.stdout.write('.')
    sys.stdout.flush()

print()
