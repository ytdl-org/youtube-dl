# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class VoissaIE(InfoExtractor):
    _VALID_URL = r'https?://communaute.voissa.com/gallery/image/(?P<id>[0-9]+)(?P<display_id>[^/]+)'
    _TESTS = [
        {
            'url': 'http://communaute.voissa.com/gallery/image/4613602-massage-a-l-huile-ds-la-baignoire/',
            'md5': 'd827e750d5eae4ce5260e6f6dcf87410',
            'info_dict': {
                'id': '4613602',
                'display_id': '-massage-a-l-huile-ds-la-baignoire',
                'ext': 'mp4',
                'title': 'massage a l huile ds la baignoire........',
                'uploader': 'exocharme',
                'thumbnail': 'http://static.voissa.fr/uploads/videos_thumbs/4613602/main.jpg',
            }
        },
        {
            'url': 'http://communaute.voissa.com/gallery/image/4750449-suivez-mon-cul/',
            'md5': 'c49a09ad32f7f8df86b416910daf10a7',
            'info_dict': {
                'id': '4750449',
                'display_id': '-suivez-mon-cul',
                'ext': 'mp4',
                'title': 'Suivez mon Cul',
                'uploader': 'LadyOulala',
                'thumbnail': 'http://static.voissa.fr/uploads/videos_thumbs/4750449/main.jpg',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, video_id)

        root = self._download_xml('http://communaute.voissa.com/playlist.php?id=' + str(video_id), video_id, 'Url info')
        group = root[0].find('item').find('{http://search.yahoo.com/mrss/}group')
        thumbnail = group.find('{http://search.yahoo.com/mrss/}thumbnail').get('url')
        contents = group.findall('{http://search.yahoo.com/mrss/}content')

        n = len(contents)
        formats = []
        for i, v in enumerate(contents):
            url = v.get('url')
            formats.append({
                'url': url,
                'format_id': self._search_regex(r'http://download\.voissa\.fr/html5/([^/]+)/', url, 'Quality'),
                'preference': n - i
            })

        title = self._search_regex(r'<title>Vidéo ([^\(]+)\s\(.+Voissa</title>', webpage, 'title')

        mobj = re.search(r'<span itemprop="name">(?P<uploader>[^<]+)</span>.+vu (?P<viewcount>\d+)', webpage)
        uploader = mobj.group('uploader')
        view_count = mobj.group('viewcount')

        if view_count:
            view_count = int(view_count)

        return {
            'id': video_id,
            'title': title,
            'display_id': display_id,
            'formats': formats,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'view_count': view_count,
        }
