from __future__ import unicode_literals

from .common import InfoExtractor


class GrouponIE(InfoExtractor):
    _VALID_URL = r'https?://www\.groupon\.com/deals/(?P<id>[^?#]+)'

    _TEST = {
        'url': 'https://www.groupon.com/deals/bikram-yoga-huntington-beach-2#ooid=tubGNycTo_9Uxg82uESj4i61EYX8nyuf',
        'info_dict': {
            'id': 'bikram-yoga-huntington-beach-2',
            'title': '$49 for 10 Yoga Classes or One Month of Unlimited Classes at Bikram Yoga Huntington Beach ($180 Value)',
            'description': 'Studio kept at 105 degrees and 40% humidity with anti-microbial and anti-slip Flotex flooring; certified instructors',
        },
        'playlist': [{
            'info_dict': {
                'id': 'tubGNycTo_9Uxg82uESj4i61EYX8nyuf',
                'ext': 'mp4',
                'title': 'Bikram Yoga Huntington Beach | Orange County',
            },
        }],
        'params': {
            'skip_download': 'HLS',
        }
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        payload = self._parse_json(self._search_regex(
            r'var\s+payload\s*=\s*(.*?);\n', webpage, 'payload'), playlist_id)
        videos = payload['carousel'].get('dealVideos', [])
        entries = []
        for v in videos:
            if v.get('provider') != 'OOYALA':
                self.report_warning(
                    '%s: Unsupported video provider %s, skipping video' %
                    (playlist_id, v.get('provider')))
                continue
            entries.append(self.url_result('ooyala:%s' % v['media']))

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'entries': entries,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
        }
