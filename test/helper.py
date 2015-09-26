from __future__ import unicode_literals

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
    write_string,
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
        _msg_header = '\033[0;33mWARNING:\033[0m'
    else:
        _msg_header = 'WARNING:'
    output = '%s %s\n' % (_msg_header, message)
    if 'b' in getattr(sys.stderr, 'mode', '') or sys.version_info[0] < 3:
        output = output.encode(preferredencoding())
    sys.stderr.write(output)


class FakeYDL(YoutubeDL):
    def __init__(self, override=None):
        # Different instances of the downloader can't share the same dictionary
        # some test set the "sublang" parameter, which would break the md5 checks.
        params = get_params(override=override)
        super(FakeYDL, self).__init__(params, auto_init=False)
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
            if re.match(regex, message):
                return
            old_report_warning(message)
        self.report_warning = types.MethodType(report_warning, self)


def gettestcases(include_onlymatching=False):
    for ie in youtube_dl.extractor.gen_extractors():
        for tc in ie.get_testcases(include_onlymatching):
            yield tc


md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()


def expect_info_dict(self, got_dict, expected_dict):
    for info_field, expected in expected_dict.items():
        if isinstance(expected, compat_str) and expected.startswith('re:'):
            got = got_dict.get(info_field)
            match_str = expected[len('re:'):]
            match_rex = re.compile(match_str)

            self.assertTrue(
                isinstance(got, compat_str),
                'Expected a %s object, but got %s for field %s' % (
                    compat_str.__name__, type(got).__name__, info_field))
            self.assertTrue(
                match_rex.match(got),
                'field %s (value: %r) should match %r' % (info_field, got, match_str))
        elif isinstance(expected, compat_str) and expected.startswith('startswith:'):
            got = got_dict.get(info_field)
            start_str = expected[len('startswith:'):]
            self.assertTrue(
                isinstance(got, compat_str),
                'Expected a %s object, but got %s for field %s' % (
                    compat_str.__name__, type(got).__name__, info_field))
            self.assertTrue(
                got.startswith(start_str),
                'field %s (value: %r) should start with %r' % (info_field, got, start_str))
        elif isinstance(expected, compat_str) and expected.startswith('contains:'):
            got = got_dict.get(info_field)
            contains_str = expected[len('contains:'):]
            self.assertTrue(
                isinstance(got, compat_str),
                'Expected a %s object, but got %s for field %s' % (
                    compat_str.__name__, type(got).__name__, info_field))
            self.assertTrue(
                contains_str in got,
                'field %s (value: %r) should contain %r' % (info_field, got, contains_str))
        elif isinstance(expected, type):
            got = got_dict.get(info_field)
            self.assertTrue(isinstance(got, expected),
                            'Expected type %r for field %s, but got value %r of type %r' % (expected, info_field, got, type(got)))
        else:
            if isinstance(expected, compat_str) and expected.startswith('md5:'):
                got = 'md5:' + md5(got_dict.get(info_field))
            elif isinstance(expected, compat_str) and expected.startswith('mincount:'):
                got = got_dict.get(info_field)
                self.assertTrue(
                    isinstance(got, (list, dict)),
                    'Expected field %s to be a list or a dict, but it is of type %s' % (
                        info_field, type(got).__name__))
                expected_num = int(expected.partition(':')[2])
                assertGreaterEqual(
                    self, len(got), expected_num,
                    'Expected %d items in field %s, but only got %d' % (
                        expected_num, info_field, len(got)
                    )
                )
                continue
            else:
                got = got_dict.get(info_field)
            self.assertEqual(expected, got,
                             'invalid value for field %s, expected %r, got %r' % (info_field, expected, got))

    # Check for the presence of mandatory fields
    if got_dict.get('_type') not in ('playlist', 'multi_video'):
        for key in ('id', 'url', 'title', 'ext'):
            self.assertTrue(got_dict.get(key), 'Missing mandatory field %s' % key)
    # Check for mandatory fields that are automatically set by YoutubeDL
    for key in ['webpage_url', 'extractor', 'extractor_key']:
        self.assertTrue(got_dict.get(key), 'Missing field: %s' % key)

    # Are checkable fields missing from the test case definition?
    test_info_dict = dict((key, value if not isinstance(value, compat_str) or len(value) < 250 else 'md5:' + md5(value))
                          for key, value in got_dict.items()
                          if value and key in ('id', 'title', 'description', 'uploader', 'upload_date', 'timestamp', 'uploader_id', 'location', 'age_limit'))
    missing_keys = set(test_info_dict.keys()) - set(expected_dict.keys())
    if missing_keys:
        def _repr(v):
            if isinstance(v, compat_str):
                return "'%s'" % v.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
            else:
                return repr(v)
        info_dict_str = ''
        if len(missing_keys) != len(expected_dict):
            info_dict_str += ''.join(
                '    %s: %s,\n' % (_repr(k), _repr(v))
                for k, v in test_info_dict.items() if k not in missing_keys)

            if info_dict_str:
                info_dict_str += '\n'
        info_dict_str += ''.join(
            '    %s: %s,\n' % (_repr(k), _repr(test_info_dict[k]))
            for k in missing_keys)
        write_string(
            '\n\'info_dict\': {\n' + info_dict_str + '},\n', out=sys.stderr)
        self.assertFalse(
            missing_keys,
            'Missing keys in test definition: %s' % (
                ', '.join(sorted(missing_keys))))


def assertRegexpMatches(self, text, regexp, msg=None):
    if hasattr(self, 'assertRegexp'):
        return self.assertRegexp(text, regexp, msg)
    else:
        m = re.match(regexp, text)
        if not m:
            note = 'Regexp didn\'t match: %r not found' % (regexp)
            if len(text) < 1000:
                note += ' in %r' % text
            if msg is None:
                msg = note
            else:
                msg = note + ', ' + msg
            self.assertTrue(m, msg)


def assertGreaterEqual(self, got, expected, msg=None):
    if not (got >= expected):
        if msg is None:
            msg = '%r not greater than or equal to %r' % (got, expected)
        self.assertTrue(got >= expected, msg)


def expect_warnings(ydl, warnings_re):
    real_warning = ydl.report_warning

    def _report_warning(w):
        if not any(re.search(w_re, w) for w_re in warnings_re):
            real_warning(w)

    ydl.report_warning = _report_warning
