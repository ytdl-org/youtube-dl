# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    url_basename,
    mimetype2ext,
    HEADRequest,
    ExtractorError
)
from ..compat import (
    compat_urllib_request,
    compat_urlparse,
    compat_str
)

import os.path
import cgi
import re


class TistoryIE(InfoExtractor):
    _VALID_URL = r'https?://cfile[0-9]*.uf.tistory.com/(?:media|attach|attachment|original)/(?P<id>[A-Za-z0-9]*)'

    _TESTS = [
        {
            'url': 'http://cfile23.uf.tistory.com/media/111ED14A4FAEBC3C23AAE1',
            'md5': '55c32cda7b1a091d75c32aeaaea47595',
            'info_dict': {
                'id': '207B594C4FAEBBC118096B',
                'title': '함친.wmv-muxed',
                'ext': 'mp4'
            },
        },
        {
            'url': 'http://cfile24.uf.tistory.com/original/1870B0374FBD97A80980D2',
            'md5': 'dad089588a30447c0e51c78f29a9183e',
            'info_dict': {
                'id': '1870B0374FBD97A80980D2',
                'title': '무제-1',
                'ext': 'flv'
            }
        }
    ]

    def unquote(self, url):
        return compat_urlparse.unquote(url)

    def get_title(self, url, response):
        _, params = cgi.parse_header(response.info().get('Content-Disposition', ''))
        if "filename" in params:
            filename = params["filename"]
        else:
            filename = url_basename(url)

        retval = os.path.splitext(self.unquote(filename))[0]

        if type(retval) != compat_str:
            retval = retval.decode('UTF-8')

        return retval

    def get_ext(self, mime):
        ext = mimetype2ext(mime)
        if ext == "x-shockwave-flash":
            ext = "flv"
        return ext

    def _real_extract(self, url):
        video_id = self._match_id(url)

        self.to_screen('%s: Downloading headers' % (video_id))
        req = HEADRequest(url)

        head = compat_urllib_request.urlopen(req)
        content_type = head.info().get("content-type")
        content_length = int(head.info().get("content-length"))

        ret = {
            "id": compat_str(video_id),
            "url": url,
            "title": self.get_title(url, head)
        }

        if content_type == "application/x-shockwave-flash" and content_length < 200000:
            swfreq = self._request_webpage(url, video_id, "Downloading SWF")
            data = swfreq.read()

            a = data[0]
            b = data[1]
            c = data[2]

            if isinstance(a, str):
                a = ord(a)
                b = ord(b)
                c = ord(c)

            rawswfdata = data[8:]

            if a not in [0x43, 0x46, 0x5A] or b != 0x57 or c != 0x53:
                raise ExtractorError("Not a SWF file")

            if a == 0x46:
                swfdata = rawswfdata
            elif a == 0x43:
                import zlib
                zip = zlib.decompressobj()
                swfdata = str(zip.decompress(rawswfdata))
            elif a == 0x5A:
                import pylzma
                rawswfdata = data[11:]
                swfdata = str(pylzma.decompress(rawswfdata))

            match = re.search("(https?://[A-Za-z0-9.]*/attachment/cfile[0-9]*.uf@[A-Za-z0-9.@%]*)",
                              swfdata)
            if not match:
                raise ExtractorError("Unable to find check URL")

            checkurl = match.group(1)

            checkmatch = re.search("(cfile[0-9]*.uf)@([A-Z0-9]*)", checkurl)
            if not checkmatch:
                raise ExtractorError("Unable to find real URL in check URL")

            cfile = checkmatch.group(1)
            url = checkmatch.group(2)

            ret["url"] = "http://" + cfile + ".tistory.com/attach/" + url
            return self._real_extract(ret["url"])
        else:
            ret["ext"] = self.get_ext(content_type)
            return ret
