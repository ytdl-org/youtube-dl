import io
import json
import os.path

import youtube_dl.extractor
from youtube_dl import YoutubeDL, YoutubeDLHandler
from youtube_dl.utils import (
    compat_cookiejar,
    compat_urllib_request,
)

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)

PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    parameters = json.load(pf)

class FakeYDL(YoutubeDL):
    def __init__(self):
        self.result = []
        # Different instances of the downloader can't share the same dictionary
        # some test set the "sublang" parameter, which would break the md5 checks.
        self.params = dict(parameters)
    def to_screen(self, s):
        print(s)
    def trouble(self, s, tb=None):
        raise Exception(s)
    def download(self, x):
        self.result.append(x)

def get_testcases():
    for ie in youtube_dl.extractor.gen_extractors():
        t = getattr(ie, '_TEST', None)
        if t:
            t['name'] = type(ie).__name__[:-len('IE')]
            yield t
        for t in getattr(ie, '_TESTS', []):
            t['name'] = type(ie).__name__[:-len('IE')]
            yield t
