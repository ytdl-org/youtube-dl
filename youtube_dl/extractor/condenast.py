# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    orderedSet,
    compat_urllib_parse_urlparse,
    compat_urlparse,
)


class CondeNastIE(InfoExtractor):
    """
    Condé Nast is a media group, some of its sites use a custom HTML5 player
    that works the same in all of them.
    """

    # The keys are the supported sites and the values are the name to be shown
    # to the user and in the extractor description.
    _SITES = {
        'wired': 'WIRED',
        'gq': 'GQ',
        'vogue': 'Vogue',
        'glamour': 'Glamour',
        'wmagazine': 'W Magazine',
        'vanityfair': 'Vanity Fair',
        'cnevids': 'Condé Nast',
    }

    _VALID_URL = r'http://(video|www|player)\.(?P<site>%s)\.com/(?P<type>watch|series|video|embed)/(?P<id>[^/?#]+)' % '|'.join(_SITES.keys())
    IE_DESC = 'Condé Nast media group: %s' % ', '.join(sorted(_SITES.values()))

    EMBED_URL = r'(?:https?:)?//player\.(?P<site>%s)\.com/(?P<type>embed)/.+?' % '|'.join(_SITES.keys())

    _TEST = {
        'url': 'http://video.wired.com/watch/3d-printed-speakers-lit-with-led',
        'md5': '1921f713ed48aabd715691f774c451f7',
        'info_dict': {
            'id': '5171b343c2b4c00dd0c1ccb3',
            'ext': 'mp4',
            'title': '3D Printed Speakers Lit With LED',
            'description': 'Check out these beautiful 3D printed LED speakers.  You can\'t actually buy them, but LumiGeek is working on a board that will let you make you\'re own.',
        }
    }

    def _extract_series(self, url, webpage):
        title = self._html_search_regex(r'<div class="cne-series-info">.*?<h1>(.+?)</h1>',
                                        webpage, 'series title', flags=re.DOTALL)
        url_object = compat_urllib_parse_urlparse(url)
        base_url = '%s://%s' % (url_object.scheme, url_object.netloc)
        m_paths = re.finditer(r'<p class="cne-thumb-title">.*?<a href="(/watch/.+?)["\?]',
                              webpage, flags=re.DOTALL)
        paths = orderedSet(m.group(1) for m in m_paths)
        build_url = lambda path: compat_urlparse.urljoin(base_url, path)
        entries = [self.url_result(build_url(path), 'CondeNast') for path in paths]
        return self.playlist_result(entries, playlist_title=title)

    def _extract_video(self, webpage, url_type):
        if url_type != 'embed':
            description = self._html_search_regex(
                [
                    r'<div class="cne-video-description">(.+?)</div>',
                    r'<div class="video-post-content">(.+?)</div>',
                ],
                webpage, 'description', fatal=False, flags=re.DOTALL)
        else:
            description = None
        params = self._search_regex(r'var params = {(.+?)}[;,]', webpage,
                                    'player params', flags=re.DOTALL)
        video_id = self._search_regex(r'videoId: [\'"](.+?)[\'"]', params, 'video id')
        player_id = self._search_regex(r'playerId: [\'"](.+?)[\'"]', params, 'player id')
        target = self._search_regex(r'target: [\'"](.+?)[\'"]', params, 'target')
        data = compat_urllib_parse.urlencode({'videoId': video_id,
                                              'playerId': player_id,
                                              'target': target,
                                              })
        base_info_url = self._search_regex(r'url = [\'"](.+?)[\'"][,;]',
                                           webpage, 'base info url',
                                           default='http://player.cnevids.com/player/loader.js?')
        info_url = base_info_url + data
        info_page = self._download_webpage(info_url, video_id,
                                           'Downloading video info')
        video_info = self._search_regex(r'var video = ({.+?});', info_page, 'video info')
        video_info = json.loads(video_info)

        formats = [{
            'format_id': '%s-%s' % (fdata['type'].split('/')[-1], fdata['quality']),
            'url': fdata['src'],
            'ext': fdata['type'].split('/')[-1],
            'quality': 1 if fdata['quality'] == 'high' else 0,
        } for fdata in video_info['sources'][0]]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_info['title'],
            'thumbnail': video_info['poster_frame'],
            'description': description,
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site = mobj.group('site')
        url_type = mobj.group('type')
        item_id = mobj.group('id')

        self.to_screen('Extracting from %s with the Condé Nast extractor' % self._SITES[site])
        webpage = self._download_webpage(url, item_id)

        if url_type == 'series':
            return self._extract_series(url, webpage)
        else:
            return self._extract_video(webpage, url_type)
