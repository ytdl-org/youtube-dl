# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_urlparse,
)
from ..utils import (
    orderedSet,
    remove_end,
    extract_attributes,
    mimetype2ext,
    determine_ext,
    int_or_none,
    parse_iso8601,
)


class CondeNastIE(InfoExtractor):
    """
    Condé Nast is a media group, some of its sites use a custom HTML5 player
    that works the same in all of them.
    """

    # The keys are the supported sites and the values are the name to be shown
    # to the user and in the extractor description.
    _SITES = {
        'allure': 'Allure',
        'architecturaldigest': 'Architectural Digest',
        'arstechnica': 'Ars Technica',
        'bonappetit': 'Bon Appétit',
        'brides': 'Brides',
        'cnevids': 'Condé Nast',
        'cntraveler': 'Condé Nast Traveler',
        'details': 'Details',
        'epicurious': 'Epicurious',
        'glamour': 'Glamour',
        'golfdigest': 'Golf Digest',
        'gq': 'GQ',
        'newyorker': 'The New Yorker',
        'self': 'SELF',
        'teenvogue': 'Teen Vogue',
        'vanityfair': 'Vanity Fair',
        'vogue': 'Vogue',
        'wired': 'WIRED',
        'wmagazine': 'W Magazine',
    }

    _VALID_URL = r'https?://(?:video|www|player)\.(?P<site>%s)\.com/(?P<type>watch|series|video|embed(?:js)?)/(?P<id>[^/?#]+)' % '|'.join(_SITES.keys())
    IE_DESC = 'Condé Nast media group: %s' % ', '.join(sorted(_SITES.values()))

    EMBED_URL = r'(?:https?:)?//player\.(?P<site>%s)\.com/(?P<type>embed(?:js)?)/.+?' % '|'.join(_SITES.keys())

    _TESTS = [{
        'url': 'http://video.wired.com/watch/3d-printed-speakers-lit-with-led',
        'md5': '1921f713ed48aabd715691f774c451f7',
        'info_dict': {
            'id': '5171b343c2b4c00dd0c1ccb3',
            'ext': 'mp4',
            'title': '3D Printed Speakers Lit With LED',
            'description': 'Check out these beautiful 3D printed LED speakers.  You can\'t actually buy them, but LumiGeek is working on a board that will let you make you\'re own.',
            'uploader': 'wired',
            'upload_date': '20130314',
            'timestamp': 1363219200,
        }
    }, {
        # JS embed
        'url': 'http://player.cnevids.com/embedjs/55f9cf8b61646d1acf00000c/5511d76261646d5566020000.js',
        'md5': 'f1a6f9cafb7083bab74a710f65d08999',
        'info_dict': {
            'id': '55f9cf8b61646d1acf00000c',
            'ext': 'mp4',
            'title': '3D printed TSA Travel Sentry keys really do open TSA locks',
            'uploader': 'arstechnica',
            'upload_date': '20150916',
            'timestamp': 1442434955,
        }
    }]

    def _extract_series(self, url, webpage):
        title = self._html_search_regex(
            r'(?s)<div class="cne-series-info">.*?<h1>(.+?)</h1>',
            webpage, 'series title')
        url_object = compat_urllib_parse_urlparse(url)
        base_url = '%s://%s' % (url_object.scheme, url_object.netloc)
        m_paths = re.finditer(
            r'(?s)<p class="cne-thumb-title">.*?<a href="(/watch/.+?)["\?]', webpage)
        paths = orderedSet(m.group(1) for m in m_paths)
        build_url = lambda path: compat_urlparse.urljoin(base_url, path)
        entries = [self.url_result(build_url(path), 'CondeNast') for path in paths]
        return self.playlist_result(entries, playlist_title=title)

    def _extract_video(self, webpage, url_type):
        query = {}
        params = self._search_regex(
            r'(?s)var params = {(.+?)}[;,]', webpage, 'player params', default=None)
        if params:
            query.update({
                'videoId': self._search_regex(r'videoId: [\'"](.+?)[\'"]', params, 'video id'),
                'playerId': self._search_regex(r'playerId: [\'"](.+?)[\'"]', params, 'player id'),
                'target': self._search_regex(r'target: [\'"](.+?)[\'"]', params, 'target'),
            })
        else:
            params = extract_attributes(self._search_regex(
                r'(<[^>]+data-js="video-player"[^>]+>)',
                webpage, 'player params element'))
            query.update({
                'videoId': params['data-video'],
                'playerId': params['data-player'],
                'target': params['id'],
            })
        video_id = query['videoId']
        video_info = None
        info_page = self._download_webpage(
            'http://player.cnevids.com/player/video.js',
            video_id, 'Downloading video info', query=query, fatal=False)
        if info_page:
            video_info = self._parse_json(self._search_regex(
                r'loadCallback\(({.+})\)', info_page, 'video info'), video_id)['video']
        else:
            info_page = self._download_webpage(
                'http://player.cnevids.com/player/loader.js',
                video_id, 'Downloading loader info', query=query)
            video_info = self._parse_json(self._search_regex(
                r'var\s+video\s*=\s*({.+?});', info_page, 'video info'), video_id)
        title = video_info['title']

        formats = []
        for fdata in video_info.get('sources', [{}])[0]:
            src = fdata.get('src')
            if not src:
                continue
            ext = mimetype2ext(fdata.get('type')) or determine_ext(src)
            quality = fdata.get('quality')
            formats.append({
                'format_id': ext + ('-%s' % quality if quality else ''),
                'url': src,
                'ext': ext,
                'quality': 1 if quality == 'high' else 0,
            })
        self._sort_formats(formats)

        info = self._search_json_ld(
            webpage, video_id, fatal=False) if url_type != 'embed' else {}
        info.update({
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': video_info.get('poster_frame'),
            'uploader': video_info.get('brand'),
            'duration': int_or_none(video_info.get('duration')),
            'tags': video_info.get('tags'),
            'series': video_info.get('series_title'),
            'season': video_info.get('season_title'),
            'timestamp': parse_iso8601(video_info.get('premiere_date')),
        })
        return info

    def _real_extract(self, url):
        site, url_type, item_id = re.match(self._VALID_URL, url).groups()

        # Convert JS embed to regular embed
        if url_type == 'embedjs':
            parsed_url = compat_urlparse.urlparse(url)
            url = compat_urlparse.urlunparse(parsed_url._replace(
                path=remove_end(parsed_url.path, '.js').replace('/embedjs/', '/embed/')))
            url_type = 'embed'

        self.to_screen('Extracting from %s with the Condé Nast extractor' % self._SITES[site])
        webpage = self._download_webpage(url, item_id)

        if url_type == 'series':
            return self._extract_series(url, webpage)
        else:
            return self._extract_video(webpage, url_type)
