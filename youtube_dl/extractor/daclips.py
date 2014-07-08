# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from gorillavid import GorillaVidIE


class DaclipsIE(GorillaVidIE):
    _HOST = 'daclips.in'
    _VALID_URL = GorillaVidIE._VALID_URL_TEMPLATE % {'host': re.escape(_HOST)}

    _TESTS = [{
        'url': 'http://daclips.in/3rso4kdn6f9m',
        'info_dict': {
            'id': '3rso4kdn6f9m',
            'ext': 'mp4',
            'title': 'Micro Pig piglets ready on 16th July 2009',
            'thumbnail': 're:http://.*\.jpg',
        },
    }]
