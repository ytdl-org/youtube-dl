import errno
import io
import hashlib
import json
import os.path
import re
import types
import sys

import youtube_dl.extractor
from youtube_dl import YoutubeDL
from youtube_dl.utils import (
    compat_str,
    preferredencoding,
)


def get_params(override=None):
    PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "parameters.json")
    with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
        parameters = json.load(pf)
    if override:
        parameters.update(override)
    return parameters


def try_rm(filename):
    """ Remove a file if it exists """
    try:
        os.remove(filename)
    except OSError as ose:
        if ose.errno != errno.ENOENT:
            raise


def report_warning(message):
    '''
    Print the message to stderr, it will be prefixed with 'WARNING:'
    If stderr is a tty file the 'WARNING:' will be colored
    '''
    if sys.stderr.isatty() and os.name != 'nt':
        _msg_header = u'\033[0;33mWARNING:\033[0m'
    else:
        _msg_header = u'WARNING:'
    output = u'%s %s\n' % (_msg_header, message)
    if 'b' in getattr(sys.stderr, 'mode', '') or sys.version_info[0] < 3:
        output = output.encode(preferredencoding())
    sys.stderr.write(output)


class FakeYDL(YoutubeDL):
    def __init__(self, override=None):
        # Different instances of the downloader can't share the same dictionary
        # some test set the "sublang" parameter, which would break the md5 checks.
        params = get_params(override=override)
        super(FakeYDL, self).__init__(params)
        self.result = []
        
    def to_screen(self, s, skip_eol=None):
        print(s)

    def trouble(self, s, tb=None):
        raise Exception(s)

    def download(self, x):
        self.result.append(x)

    def expect_warning(self, regex):
        # Silence an expected warning matching a regex
        old_report_warning = self.report_warning
        def report_warning(self, message):
            if re.match(regex, message): return
            old_report_warning(message)
        self.report_warning = types.MethodType(report_warning, self)

def gettestcases():
    for ie in youtube_dl.extractor.gen_extractors():
        t = getattr(ie, '_TEST', None)
        if t:
            t['name'] = type(ie).__name__[:-len('IE')]
            yield t
        for t in getattr(ie, '_TESTS', []):
            t['name'] = type(ie).__name__[:-len('IE')]
            yield t


md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()


def expect_info_dict(self, expected_dict, got_dict):
    for info_field, expected in expected_dict.items():
        if isinstance(expected, compat_str) and expected.startswith('re:'):
            got = got_dict.get(info_field)
            match_str = expected[len('re:'):]
            match_rex = re.compile(match_str)

            self.assertTrue(
                isinstance(got, compat_str) and match_rex.match(got),
                u'field %s (value: %r) should match %r' % (info_field, got, match_str))
        elif isinstance(expected, type):
            got = got_dict.get(info_field)
            self.assertTrue(isinstance(got, expected),
                u'Expected type %r, but got value %r of type %r' % (expected, got, type(got)))
        else:
            if isinstance(expected, compat_str) and expected.startswith('md5:'):
                got = 'md5:' + md5(got_dict.get(info_field))
            else:
                got = got_dict.get(info_field)
            self.assertEqual(expected, got,
                u'invalid value for field %s, expected %r, got %r' % (info_field, expected, got))

