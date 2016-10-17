from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    float_or_none,
    int_or_none,
)


class PlaywireIE(InfoExtractor):
    _VALID_URL = r'https?://(?:config|cdn)\.playwire\.com(?:/v2)?/(?P<publisher_id>\d+)/(?:videos/v2|embed|config)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://config.playwire.com/14907/videos/v2/3353705/player.json',
        'md5': 'e6398701e3595888125729eaa2329ed9',
        'info_dict': {
            'id': '3353705',
            'ext': 'mp4',
            'title': 'S04_RM_UCL_Rus',
            'thumbnail': 're:^https?://.*\.png$',
            'duration': 145.94,
        },
    }, {
        'url': 'http://cdn.playwire.com/11625/embed/85228.html',
        'only_matching': True,
    }, {
        'url': 'http://config.playwire.com/12421/videos/v2/3389892/zeus.json',
        'only_matching': True,
    }, {
        'url': 'http://cdn.playwire.com/v2/12342/config/1532636.json',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        publisher_id, video_id = mobj.group('publisher_id'), mobj.group('id')

        player = self._download_json(
            'http://config.playwire.com/%s/videos/v2/%s/zeus.json' % (publisher_id, video_id),
            video_id)

        title = player['settings']['title']
        duration = float_or_none(player.get('duration'), 1000)

        content = player['content']
        thumbnail = content.get('poster')
        src = content['media']['f4m']

        f4m = self._download_xml(src, video_id)
        base_url = xpath_text(f4m, './{http://ns.adobe.com/f4m/1.0}baseURL', 'base url', fatal=True)
        formats = []
        for media in f4m.findall('./{http://ns.adobe.com/f4m/1.0}media'):
            media_url = media.get('url')
            if not media_url:
                continue
            tbr = int_or_none(media.get('bitrate'))
            width = int_or_none(media.get('width'))
            height = int_or_none(media.get('height'))
            f = {
                'url': '%s/%s' % (base_url, media.attrib['url']),
                'tbr': tbr,
                'width': width,
                'height': height,
            }
            if not (tbr or width or height):
                f['quality'] = 1 if '-hd.' in media_url else 0
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
