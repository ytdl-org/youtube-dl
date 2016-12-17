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
    compat_urllib_error,
    compat_urlparse,
    compat_str
)

import os.path
import cgi
import re
import xml.etree.ElementTree as ET


class TistoryBaseIE(InfoExtractor):
    _TI_MEDIA_URL = r'https?://cfile[0-9]*.uf.tistory.com/(?:media|attach|attachment|original)/(?P<id>[A-Za-z0-9]*)'

    def _ti_unquote(self, url):
        return compat_urlparse.unquote(url)

    def _ti_get_title(self, url, response):
        _, params = cgi.parse_header(response.info().get('Content-Disposition', ''))
        if "filename" in params:
            filename = params["filename"]
        else:
            filename = url_basename(url)

        retval = os.path.splitext(self._ti_unquote(filename))[0]

        if type(retval) != compat_str:
            retval = retval.decode('UTF-8')

        return retval

    def _ti_get_ext(self, mime):
        ext = mimetype2ext(mime)
        if ext == "x-shockwave-flash":
            ext = "flv"
        return ext

    def _ti_get_real_from_check(self, check):
        checkmatch = re.search("(cfile[0-9]*.uf)@([A-Z0-9]*)(?:\.([A-Za-z0-9]*))?", check)
        if not checkmatch:
            return None

        cfile = checkmatch.group(1)
        url = checkmatch.group(2)
        ext = None

        if len(checkmatch.groups()) > 2:
            ext = checkmatch.group(3)

        return ("http://" + cfile + ".tistory.com/attach/" + url, ext)

    def _ti_get_video_id(self, url):
        if '_TI_MEDIA_URL_RE' not in self.__dict__:
            self._TI_MEDIA_URL_RE = re.compile(self._TI_MEDIA_URL)
        m = self._TI_MEDIA_URL_RE.match(url)
        assert m
        return m.group('id')

    def _ti_get_headers(self, url, video_id):
        self.to_screen('%s: Downloading headers' % (video_id))
        req = HEADRequest(url)

        return compat_urllib_request.urlopen(req)

    def _ti_detect_swf(self, head):
        content_type = head.info().get("content-type")
        content_length = int(head.info().get("content-length"))

        if content_type == "application/x-shockwave-flash" and content_length < 200000:
            return True

        return False

    def _ti_get_media(self, url, video_id, head, ext=None, title=None):
        if head:
            content_type = head.info().get("content-type")
            ext = self._ti_get_ext(content_type)
            title = self._ti_get_title(url, head)

        if not title:
            title = video_id

        return {
            "id": compat_str(video_id),
            "url": url,
            "title": title,
            "ext": ext
        }

    def _ti_read_swf(self, url, video_id, head):
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

        real_url, ext = self._ti_get_real_from_check(checkurl)
        if not real_url:
            raise ExtractorError("Unable to find real URL in check URL")

        return (real_url, ext)

    def _ti_dl(self, url, ext=None, title=None):
        video_id = self._ti_get_video_id(url)

        head = None

        try:
            head = self._ti_get_headers(url, video_id)
        except compat_urllib_error.HTTPError:
            pass
        except Exception:
            head = None

        if head and self._ti_detect_swf(head):
            return self._ti_dl(*self._ti_read_swf(url, video_id, head))
        else:
            return self._ti_get_media(url, video_id, head, ext, title)


class TistoryIE(TistoryBaseIE):
    _VALID_URL = TistoryBaseIE._TI_MEDIA_URL

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

    def _real_extract(self, url):
        return self._ti_dl(url)


class TistoryPlaylistIE(TistoryBaseIE):
    _VALID_URL = r'(?:https?://cfs.tistory.com/custom/blog/.*/skin/images/po.swf?.*file=)?(?P<rurl>https?://cfs.tistory.com/custom/blog/.*/skin/images/(?P<id>.*)\.xml).*'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        rurl = self._VALID_URL_RE.match(url).group("rurl")

        xml = self._download_xml(rurl, video_id)
        entries = []

        for tracklist in xml:
            for track in tracklist:
                for tag in track:
                    print(ET.tostring(tag))
                    if "location" not in tag.tag:
                        continue

                    loc = tag.text

                    newloc, ext = self._ti_get_real_from_check(loc)
                    if newloc:
                        loc = newloc

                    entries.append(self._ti_dl(loc, ext))


        return self.playlist_result(entries)
