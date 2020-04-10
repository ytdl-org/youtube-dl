# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unescapeHTML, ExtractorError

import re


class KnessetGovIlIE(InfoExtractor):
    _VALID_URL = r'https://main\.knesset\.gov\.il/Activity/committees/(?P<committee>[^/]+)/Pages/CommitteeTVarchive\.aspx\?TopicID=(?P<topicid>[0-9]+)'
    _TEST = {
        'url': 'https://main.knesset.gov.il/Activity/committees/CoronaVirus/Pages/CommitteeTVarchive.aspx?TopicID=19932',
        'only_matching': True
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = '-'.join(m.groups())

        self._download_webpage(url, video_id, note='Getting cookie')
        webpage = self._download_webpage(
            url,
            video_id,
            headers=self._get_cookies(url)
        )

        m = re.search(
            r"SetAzurePlayerFileName\(\'(?P<mpd>[^']+)\',\s*\'(?P<title>[^']+)\',\s*\'(?P<date>[^']+)\'",
            webpage
        )
        if not m:
            raise ExtractorError('Video not found at url')

        data = m.groupdict()

        return {
            'id': video_id,
            'title': unescapeHTML(data['title']).strip(),
            'description': unescapeHTML(data['date']).strip(),
            'formats': self._extract_mpd_formats(
                unescapeHTML(data['mpd']),
                video_id,
                'dash'
            )
        }
