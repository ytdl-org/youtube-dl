#!/usr/bin/env python

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import (
    get_params,
    gettestcases,
    try_rm,
    md5,
    report_warning
)


import hashlib
import io
import json
import re
import socket

import youtube_dl.YoutubeDL
from youtube_dl.utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_HTTPError,
    DownloadError,
    ExtractorError,
    UnavailableVideoError,
)
from youtube_dl.extractor import get_info_extractor

RETRIES = 3

class YoutubeDL(youtube_dl.YoutubeDL):
    def __init__(self, *args, **kwargs):
        self.to_stderr = self.to_screen
        self.processed_info_dicts = []
        super(YoutubeDL, self).__init__(*args, **kwargs)
    def report_warning(self, message):
        # Don't accept warnings during tests
        raise ExtractorError(message)
    def process_info(self, info_dict):
        self.processed_info_dicts.append(info_dict)
        return super(YoutubeDL, self).process_info(info_dict)

def _file_md5(fn):
    with open(fn, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

defs = gettestcases()


class TestDownload(unittest.TestCase):
    maxDiff = None
    def setUp(self):
        self.defs = defs

### Dynamically generate tests
def generator(test_case):

    def test_template(self):
        ie = youtube_dl.extractor.get_info_extractor(test_case['name'])
        other_ies = [get_info_extractor(ie_key) for ie_key in test_case.get('add_ie', [])]
        def print_skipping(reason):
            print('Skipping %s: %s' % (test_case['name'], reason))
        if not ie.working():
            print_skipping('IE marked as not _WORKING')
            return
        if 'playlist' not in test_case:
            info_dict = test_case.get('info_dict', {})
            if not test_case.get('file') and not (info_dict.get('id') and info_dict.get('ext')):
                raise Exception('Test definition incorrect. The output file cannot be known. Are both \'id\' and \'ext\' keys present?')
        if 'skip' in test_case:
            print_skipping(test_case['skip'])
            return
        for other_ie in other_ies:
            if not other_ie.working():
                print_skipping(u'test depends on %sIE, marked as not WORKING' % other_ie.ie_key())
                return

        params = get_params(test_case.get('params', {}))

        ydl = YoutubeDL(params)
        ydl.add_default_info_extractors()
        finished_hook_called = set()
        def _hook(status):
            if status['status'] == 'finished':
                finished_hook_called.add(status['filename'])
        ydl.add_progress_hook(_hook)

        def get_tc_filename(tc):
            return tc.get('file') or ydl.prepare_filename(tc.get('info_dict', {}))

        test_cases = test_case.get('playlist', [test_case])
        def try_rm_tcs_files():
            for tc in test_cases:
                tc_filename = get_tc_filename(tc)
                try_rm(tc_filename)
                try_rm(tc_filename + '.part')
                try_rm(os.path.splitext(tc_filename)[0] + '.info.json')
        try_rm_tcs_files()
        try:
            try_num = 1
            while True:
                try:
                    ydl.download([test_case['url']])
                except (DownloadError, ExtractorError) as err:
                    # Check if the exception is not a network related one
                    if not err.exc_info[0] in (compat_urllib_error.URLError, socket.timeout, UnavailableVideoError, compat_http_client.BadStatusLine) or (err.exc_info[0] == compat_HTTPError and err.exc_info[1].code == 503):
                        raise

                    if try_num == RETRIES:
                        report_warning(u'Failed due to network errors, skipping...')
                        return

                    print('Retrying: {0} failed tries\n\n##########\n\n'.format(try_num))

                    try_num += 1
                else:
                    break

            for tc in test_cases:
                tc_filename = get_tc_filename(tc)
                if not test_case.get('params', {}).get('skip_download', False):
                    self.assertTrue(os.path.exists(tc_filename), msg='Missing file ' + tc_filename)
                    self.assertTrue(tc_filename in finished_hook_called)
                info_json_fn = os.path.splitext(tc_filename)[0] + '.info.json'
                self.assertTrue(os.path.exists(info_json_fn))
                if 'md5' in tc:
                    md5_for_file = _file_md5(tc_filename)
                    self.assertEqual(md5_for_file, tc['md5'])
                with io.open(info_json_fn, encoding='utf-8') as infof:
                    info_dict = json.load(infof)
                for (info_field, expected) in tc.get('info_dict', {}).items():
                    if isinstance(expected, compat_str) and expected.startswith('re:'):
                        got = info_dict.get(info_field)
                        match_str = expected[len('re:'):]
                        match_rex = re.compile(match_str)

                        self.assertTrue(
                            isinstance(got, compat_str) and match_rex.match(got),
                            u'field %s (value: %r) should match %r' % (info_field, got, match_str))
                    elif isinstance(expected, type):
                        got = info_dict.get(info_field)
                        self.assertTrue(isinstance(got, expected),
                            u'Expected type %r, but got value %r of type %r' % (expected, got, type(got)))
                    else:
                        if isinstance(expected, compat_str) and expected.startswith('md5:'):
                            got = 'md5:' + md5(info_dict.get(info_field))
                        else:
                            got = info_dict.get(info_field)
                        self.assertEqual(expected, got,
                            u'invalid value for field %s, expected %r, got %r' % (info_field, expected, got))

                # Check for the presence of mandatory fields
                for key in ('id', 'url', 'title', 'ext'):
                    self.assertTrue(key in info_dict.keys() and info_dict[key])
                # Check for mandatory fields that are automatically set by YoutubeDL
                for key in ['webpage_url', 'extractor', 'extractor_key']:
                    self.assertTrue(info_dict.get(key), u'Missing field: %s' % key)

                # Are checkable fields missing from the test case definition?
                test_info_dict = dict((key, value if not isinstance(value, compat_str) or len(value) < 250 else 'md5:' + md5(value))
                    for key, value in info_dict.items()
                    if value and key in ('title', 'description', 'uploader', 'upload_date', 'timestamp', 'uploader_id', 'location'))
                missing_keys = set(test_info_dict.keys()) - set(tc.get('info_dict', {}).keys())
                if missing_keys:
                    sys.stderr.write(u'\n"info_dict": ' + json.dumps(test_info_dict, ensure_ascii=False, indent=4) + u'\n')
                    self.assertFalse(
                        missing_keys,
                        'Missing keys in test definition: %s' % (
                            ','.join(sorted(missing_keys))))
        finally:
            try_rm_tcs_files()

    return test_template

### And add them to TestDownload
for n, test_case in enumerate(defs):
    test_method = generator(test_case)
    tname = 'test_' + str(test_case['name'])
    i = 1
    while hasattr(TestDownload, tname):
        tname = 'test_'  + str(test_case['name']) + '_' + str(i)
        i += 1
    test_method.__name__ = tname
    setattr(TestDownload, test_method.__name__, test_method)
    del test_method


if __name__ == '__main__':
    unittest.main()
