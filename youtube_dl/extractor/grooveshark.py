# coding: utf-8
from __future__ import unicode_literals

import time
import math
import re

from urllib import quote, urlencode
from os.path import basename

from .common import InfoExtractor
from ..utils import ExtractorError, compat_urllib_request, compat_html_parser

from ..utils import compat_urlparse
urlparse = compat_urlparse.urlparse
urlunparse = compat_urlparse.urlunparse
urldefrag = compat_urlparse.urldefrag


class GroovesharkHtmlParser(compat_html_parser.HTMLParser):
    def __init__(self):
        self._current_object = None
        self.objects = []
        compat_html_parser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        attrs = dict((k, v) for k, v in attrs)
        if tag == 'object':
            self._current_object = {'attrs': attrs, 'params': []}
        elif tag == 'param':
            self._current_object['params'].append(attrs)

    def handle_endtag(self, tag):
        if tag == 'object':
            self.objects.append(self._current_object)
            self._current_object = None

    @classmethod
    def extract_object_tags(cls, html):
        p = cls()
        p.feed(html)
        p.close()
        return p.objects


class GroovesharkIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?grooveshark\.com/#!/s/([^/]+)/([^/]+)'
    _TEST = {
        'url': 'http://grooveshark.com/#!/s/Jolene+Tenth+Key+Remix+Ft+Will+Sessions/6SS1DW?src=5',
        'md5': 'bbccc50b19daca23b8f961152c1dc95b',
        'info_dict': {
            'id': '6SS1DW',
            'title': 'Jolene (Tenth Key Remix ft. Will Sessions)',
            'ext': 'mp3',
            'duration': 227
        }
    }

    do_playerpage_request = True
    do_bootstrap_request = True

    def _parse_target(self, target):
        uri = urlparse(target)
        hash = uri.fragment[1:].split('?')[0]
        token = basename(hash.rstrip('/'))
        return (uri, hash, token)

    def _build_bootstrap_url(self, target):
        (uri, hash, token) = self._parse_target(target)
        query = 'getCommunicationToken=1&hash=%s&%d' % (quote(hash, safe=''), self.ts)
        return (urlunparse((uri.scheme, uri.netloc, '/preload.php', None, query, None)), token)

    def _build_meta_url(self, target):
        (uri, hash, token) = self._parse_target(target)
        query = 'hash=%s&%d' % (quote(hash, safe=''), self.ts)
        return (urlunparse((uri.scheme, uri.netloc, '/preload.php', None, query, None)), token)

    def _build_stream_url(self, meta):
        return urlunparse(('http', meta['streamKey']['ip'], '/stream.php', None, None, None))

    def _build_swf_referer(self, target, obj):
        (uri, _, _) = self._parse_target(target)
        return urlunparse((uri.scheme, uri.netloc, obj['attrs']['data'], None, None, None))

    def _transform_bootstrap(self, js):
        return re.split('(?m)^\s*try\s*{', js)[0] \
                 .split(' = ', 1)[1].strip().rstrip(';')

    def _transform_meta(self, js):
        return js.split('\n')[0].split('=')[1].rstrip(';')

    def _get_meta(self, target):
        (meta_url, token) = self._build_meta_url(target)
        self.to_screen('Metadata URL: %s' % meta_url)

        headers = {'Referer': urldefrag(target)[0]}
        req = compat_urllib_request.Request(meta_url, headers=headers)
        res = self._download_json(req, token,
                                  transform_source=self._transform_meta)

        if 'getStreamKeyWithSong' not in res:
            raise ExtractorError(
                'Metadata not found. URL may be malformed, or Grooveshark API may have changed.')

        if res['getStreamKeyWithSong'] is None:
            raise ExtractorError(
                'Metadata download failed, probably due to Grooveshark anti-abuse throttling. Wait at least an hour before retrying from this IP.',
                expected=True)

        return res['getStreamKeyWithSong']

    def _get_bootstrap(self, target):
        (bootstrap_url, token) = self._build_bootstrap_url(target)

        headers = {'Referer': urldefrag(target)[0]}
        req = compat_urllib_request.Request(bootstrap_url, headers=headers)
        res = self._download_json(req, token, fatal=False,
                                  note='Downloading player bootstrap data',
                                  errnote='Unable to download player bootstrap data',
                                  transform_source=self._transform_bootstrap)
        return res

    def _get_playerpage(self, target):
        (_, _, token) = self._parse_target(target)

        res = self._download_webpage(
            target, token,
            note='Downloading player page',
            errnote='Unable to download player page',
            fatal=False)

        if res is not None:
            o = GroovesharkHtmlParser.extract_object_tags(res)
            return (res, [x for x in o if x['attrs']['id'] == 'jsPlayerEmbed'])

        return (res, None)

    def _real_extract(self, url):
        (target_uri, _, token) = self._parse_target(url)

        # 1. Fill cookiejar by making a request to the player page
        if self.do_playerpage_request:
            (_, player_objs) = self._get_playerpage(url)
            if player_objs is not None:
                swf_referer = self._build_swf_referer(url, player_objs[0])
                self.to_screen('SWF Referer: %s' % swf_referer)

        # 2. Ask preload.php for swf bootstrap data to better mimic webapp
        if self.do_bootstrap_request:
            bootstrap = self._get_bootstrap(url)
            self.to_screen('CommunicationToken: %s' % bootstrap['getCommunicationToken'])

        # 3. Ask preload.php for track metadata.
        meta = self._get_meta(url)

        # 4. Construct stream request for track.
        stream_url = self._build_stream_url(meta)
        duration = int(math.ceil(float(meta['streamKey']['uSecs']) / 1000000))
        post_dict = {'streamKey': meta['streamKey']['streamKey']}
        post_data = urlencode(post_dict).encode('utf-8')
        headers = {
            'Content-Length': len(post_data),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        if 'swf_referer' in locals():
            headers['Referer'] = swf_referer

        info_dict = {
            'id': token,
            'title': meta['song']['Name'],
            'http_method': 'POST',
            'url': stream_url,
            'ext': 'mp3',
            'format': 'mp3 audio',
            'duration': duration,

            # various ways of supporting the download request.
            # remove keys unnecessary to the eventual post implementation
            'post_data': post_data,
            'post_dict': post_dict,
            'headers': headers
        }

        if 'swf_referer' in locals():
            info_dict['http_referer'] = swf_referer

        return info_dict

    def _real_initialize(self):
        self.ts = int(time.time() * 1000)  # timestamp in millis

    def _download_json(self, url_or_request, video_id,
                       note=u'Downloading JSON metadata',
                       errnote=u'Unable to download JSON metadata',
                       fatal=True,
                       transform_source=None):
        try:
            out = super(GroovesharkIE, self)._download_json(
                url_or_request, video_id, note, errnote, transform_source)
            return out
        except ExtractorError as ee:
            if fatal:
                raise ee
        return None
