# coding: utf-8
from __future__ import unicode_literals

import time
import math
import os.path
import re


from .common import InfoExtractor
from ..compat import (
    compat_html_parser,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
)
from ..utils import ExtractorError


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
        'md5': '7ecf8aefa59d6b2098517e1baa530023',
        'info_dict': {
            'id': '6SS1DW',
            'title': 'Jolene (Tenth Key Remix ft. Will Sessions)',
            'ext': 'mp3',
            'duration': 227,
        }
    }

    do_playerpage_request = True
    do_bootstrap_request = True

    def _parse_target(self, target):
        uri = compat_urlparse.urlparse(target)
        hash = uri.fragment[1:].split('?')[0]
        token = os.path.basename(hash.rstrip('/'))
        return (uri, hash, token)

    def _build_bootstrap_url(self, target):
        (uri, hash, token) = self._parse_target(target)
        query = 'getCommunicationToken=1&hash=%s&%d' % (compat_urllib_parse.quote(hash, safe=''), self.ts)
        return (compat_urlparse.urlunparse((uri.scheme, uri.netloc, '/preload.php', None, query, None)), token)

    def _build_meta_url(self, target):
        (uri, hash, token) = self._parse_target(target)
        query = 'hash=%s&%d' % (compat_urllib_parse.quote(hash, safe=''), self.ts)
        return (compat_urlparse.urlunparse((uri.scheme, uri.netloc, '/preload.php', None, query, None)), token)

    def _build_stream_url(self, meta):
        return compat_urlparse.urlunparse(('http', meta['streamKey']['ip'], '/stream.php', None, None, None))

    def _build_swf_referer(self, target, obj):
        (uri, _, _) = self._parse_target(target)
        return compat_urlparse.urlunparse((uri.scheme, uri.netloc, obj['attrs']['data'], None, None, None))

    def _transform_bootstrap(self, js):
        return re.split('(?m)^\s*try\s*{', js)[0] \
                 .split(' = ', 1)[1].strip().rstrip(';')

    def _transform_meta(self, js):
        return js.split('\n')[0].split('=')[1].rstrip(';')

    def _get_meta(self, target):
        (meta_url, token) = self._build_meta_url(target)
        self.to_screen('Metadata URL: %s' % meta_url)

        headers = {'Referer': compat_urlparse.urldefrag(target)[0]}
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

        headers = {'Referer': compat_urlparse.urldefrag(target)[0]}
        req = compat_urllib_request.Request(bootstrap_url, headers=headers)
        res = self._download_json(req, token, fatal=False,
                                  note='Downloading player bootstrap data',
                                  errnote='Unable to download player bootstrap data',
                                  transform_source=self._transform_bootstrap)
        return res

    def _get_playerpage(self, target):
        (_, _, token) = self._parse_target(target)

        webpage = self._download_webpage(
            target, token,
            note='Downloading player page',
            errnote='Unable to download player page',
            fatal=False)

        if webpage is not None:
            # Search (for example German) error message
            error_msg = self._html_search_regex(
                r'<div id="content">\s*<h2>(.*?)</h2>', webpage,
                'error message', default=None)
            if error_msg is not None:
                error_msg = error_msg.replace('\n', ' ')
                raise ExtractorError('Grooveshark said: %s' % error_msg)

        if webpage is not None:
            o = GroovesharkHtmlParser.extract_object_tags(webpage)
            return (webpage, [x for x in o if x['attrs']['id'] == 'jsPlayerEmbed'])

        return (webpage, None)

    def _real_initialize(self):
        self.ts = int(time.time() * 1000)  # timestamp in millis

    def _real_extract(self, url):
        (target_uri, _, token) = self._parse_target(url)

        # 1. Fill cookiejar by making a request to the player page
        swf_referer = None
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
        post_data = compat_urllib_parse.urlencode(post_dict).encode('utf-8')
        headers = {
            'Content-Length': len(post_data),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if swf_referer is not None:
            headers['Referer'] = swf_referer

        return {
            'id': token,
            'title': meta['song']['Name'],
            'http_method': 'POST',
            'url': stream_url,
            'ext': 'mp3',
            'format': 'mp3 audio',
            'duration': duration,
            'http_post_data': post_data,
            'http_headers': headers,
        }
