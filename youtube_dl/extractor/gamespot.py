from __future__ import unicode_literals

import re

from .once import OnceIE
from ..compat import (
    compat_urllib_parse_unquote,
)
from ..utils import (
    unescapeHTML,
    url_basename,
    dict_get,
)


class GameSpotIE(OnceIE):
    _VALID_URL = r'https?://(?:www\.)?gamespot\.com/.*-(?P<id>\d+)/?'
    _TESTS = [{
        'url': 'http://www.gamespot.com/videos/arma-3-community-guide-sitrep-i/2300-6410818/',
        'md5': 'b2a30deaa8654fcccd43713a6b6a4825',
        'info_dict': {
            'id': 'gs-2300-6410818',
            'ext': 'mp4',
            'title': 'Arma 3 - Community Guide: SITREP I',
            'description': 'Check out this video where some of the basics of Arma 3 is explained.',
        },
    }, {
        'url': 'http://www.gamespot.com/videos/the-witcher-3-wild-hunt-xbox-one-now-playing/2300-6424837/',
        'info_dict': {
            'id': 'gs-2300-6424837',
            'ext': 'mp4',
            'title': 'Now Playing - The Witcher 3: Wild Hunt',
            'description': 'Join us as we take a look at the early hours of The Witcher 3: Wild Hunt and more.',
        },
        'params': {
            'skip_download': True,  # m3u8 downloads
        },
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        data_video_json = self._search_regex(
            r'data-video=["\'](.*?)["\']', webpage, 'data video')
        data_video = self._parse_json(unescapeHTML(data_video_json), page_id)
        streams = data_video['videoStreams']

        manifest_url = None
        formats = []
        f4m_url = streams.get('f4m_stream')
        if f4m_url:
            manifest_url = f4m_url
            formats.extend(self._extract_f4m_formats(
                f4m_url + '?hdcore=3.7.0', page_id, f4m_id='hds', fatal=False))
        m3u8_url = streams.get('m3u8_stream')
        if m3u8_url:
            manifest_url = m3u8_url
            m3u8_formats = self._extract_m3u8_formats(
                m3u8_url, page_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False)
            formats.extend(m3u8_formats)
        progressive_url = dict_get(
            streams, ('progressive_hd', 'progressive_high', 'progressive_low'))
        if progressive_url and manifest_url:
            qualities_basename = self._search_regex(
                r'/([^/]+)\.csmil/',
                manifest_url, 'qualities basename', default=None)
            if qualities_basename:
                QUALITIES_RE = r'((,\d+)+,?)'
                qualities = self._search_regex(
                    QUALITIES_RE, qualities_basename,
                    'qualities', default=None)
                if qualities:
                    qualities = list(map(lambda q: int(q), qualities.strip(',').split(',')))
                    qualities.sort()
                    http_template = re.sub(QUALITIES_RE, r'%d', qualities_basename)
                    http_url_basename = url_basename(progressive_url)
                    if m3u8_formats:
                        self._sort_formats(m3u8_formats)
                        m3u8_formats = list(filter(
                            lambda f: f.get('vcodec') != 'none', m3u8_formats))
                    if len(qualities) == len(m3u8_formats):
                        for q, m3u8_format in zip(qualities, m3u8_formats):
                            f = m3u8_format.copy()
                            f.update({
                                'url': progressive_url.replace(
                                    http_url_basename, http_template % q),
                                'format_id': f['format_id'].replace('hls', 'http'),
                                'protocol': 'http',
                            })
                            formats.append(f)
                    else:
                        for q in qualities:
                            formats.append({
                                'url': progressive_url.replace(
                                    http_url_basename, http_template % q),
                                'ext': 'mp4',
                                'format_id': 'http-%d' % q,
                                'tbr': q,
                            })

        onceux_json = self._search_regex(
            r'data-onceux-options=["\'](.*?)["\']', webpage, 'data video', default=None)
        if onceux_json:
            onceux_url = self._parse_json(unescapeHTML(onceux_json), page_id).get('metadataUri')
            if onceux_url:
                formats.extend(self._extract_once_formats(re.sub(
                    r'https?://[^/]+', 'http://once.unicornmedia.com', onceux_url).replace('ads/vmap/', '')))

        if not formats:
            for quality in ['sd', 'hd']:
                # It's actually a link to a flv file
                flv_url = streams.get('f4m_{0}'.format(quality))
                if flv_url is not None:
                    formats.append({
                        'url': flv_url,
                        'ext': 'flv',
                        'format_id': quality,
                    })
        self._sort_formats(formats)

        return {
            'id': data_video['guid'],
            'display_id': page_id,
            'title': compat_urllib_parse_unquote(data_video['title']),
            'formats': formats,
            'description': self._html_search_meta('description', webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
