#!/usr/bin/env python

import errno
import hashlib
import io
import os
import json
import unittest
import sys
import socket
import binascii

# Allow direct execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_dl.FileDownloader
import youtube_dl.extractor
from youtube_dl.utils import *

DEF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests.json')
PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")

RETRIES = 3

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)
socket.setdefaulttimeout(10)

def _try_rm(filename):
    """ Remove a file if it exists """
    try:
        os.remove(filename)
    except OSError as ose:
        if ose.errno != errno.ENOENT:
            raise

md5 = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()

class FileDownloader(youtube_dl.FileDownloader):
    def __init__(self, *args, **kwargs):
        self.to_stderr = self.to_screen
        self.processed_info_dicts = []
        return youtube_dl.FileDownloader.__init__(self, *args, **kwargs)
    def report_warning(self, message):
        # Don't accept warnings during tests
        raise ExtractorError(message)
    def process_info(self, info_dict):
        self.processed_info_dicts.append(info_dict)
        return youtube_dl.FileDownloader.process_info(self, info_dict)

def _file_md5(fn):
    with open(fn, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

with io.open(DEF_FILE, encoding='utf-8') as deff:
    defs = json.load(deff)
with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    parameters = json.load(pf)


class TestDownload(unittest.TestCase):
    maxDiff = None
    def setUp(self):
        self.parameters = parameters
        self.defs = defs

### Dynamically generate tests
def generator(test_case):

    def test_template(self):
        ie = youtube_dl.extractor.get_info_extractor(test_case['name'])
        if not ie._WORKING:
            print('Skipping: IE marked as not _WORKING')
            return
        if 'playlist' not in test_case and not test_case['file']:
            print('Skipping: No output file specified')
            return
        if 'skip' in test_case:
            print('Skipping: {0}'.format(test_case['skip']))
            return

        params = self.parameters.copy()
        params.update(test_case.get('params', {}))

        fd = FileDownloader(params)
        for ie in youtube_dl.extractor.gen_extractors():
            fd.add_info_extractor(ie)
        finished_hook_called = set()
        def _hook(status):
            if status['status'] == 'finished':
                finished_hook_called.add(status['filename'])
        fd.add_progress_hook(_hook)

        test_cases = test_case.get('playlist', [test_case])
        for tc in test_cases:
            _try_rm(tc['file'])
            _try_rm(tc['file'] + '.part')
            _try_rm(tc['file'] + '.info.json')
        try:
            for retry in range(1, RETRIES + 1):
                try:
                    fd.download([test_case['url']])
                except (DownloadError, ExtractorError) as err:
                    if retry == RETRIES: raise

                    # Check if the exception is not a network related one
                    if not err.exc_info[0] in (compat_urllib_error.URLError, socket.timeout, UnavailableVideoError):
                        raise

                    print('Retrying: {0} failed tries\n\n##########\n\n'.format(retry))
                else:
                    break

            for tc in test_cases:
                if not test_case.get('params', {}).get('skip_download', False):
                    self.assertTrue(os.path.exists(tc['file']), msg='Missing file ' + tc['file'])
                    self.assertTrue(tc['file'] in finished_hook_called)
                self.assertTrue(os.path.exists(tc['file'] + '.info.json'))
                if 'md5' in tc:
                    md5_for_file = _file_md5(tc['file'])
                    self.assertEqual(md5_for_file, tc['md5'])
                with io.open(tc['file'] + '.info.json', encoding='utf-8') as infof:
                    info_dict = json.load(infof)
                for (info_field, expected) in tc.get('info_dict', {}).items():
                    if isinstance(expected, compat_str) and expected.startswith('md5:'):
                        self.assertEqual(expected, 'md5:' + md5(info_dict.get(info_field)))
                    else:
                        got = info_dict.get(info_field)
                        self.assertEqual(
                            expected, got,
                            u'invalid value for field %s, expected %r, got %r' % (info_field, expected, got))

                # If checkable fields are missing from the test case, print the info_dict
                test_info_dict = dict((key, value if not isinstance(value, compat_str) or len(value) < 250 else 'md5:' + md5(value))
                    for key, value in info_dict.items()
                    if value and key in ('title', 'description', 'uploader', 'upload_date', 'uploader_id', 'location'))
                if not all(key in tc.get('info_dict', {}).keys() for key in test_info_dict.keys()):
                    sys.stderr.write(u'\n"info_dict": ' + json.dumps(test_info_dict, ensure_ascii=False, indent=2) + u'\n')

                # Check for the presence of mandatory fields
                for key in ('id', 'url', 'title', 'ext'):
                    self.assertTrue(key in info_dict.keys() and info_dict[key])
        finally:
            for tc in test_cases:
                _try_rm(tc['file'])
                _try_rm(tc['file'] + '.part')
                _try_rm(tc['file'] + '.info.json')

    return test_template

### And add them to TestDownload
for test_case in defs:
    test_method = generator(test_case)
    test_method.__name__ = "test_{0}".format(test_case["name"])
    setattr(TestDownload, test_method.__name__, test_method)
    del test_method


if __name__ == '__main__':
    unittest.main()
