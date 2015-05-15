# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    unified_strdate,
    int_or_none,
)


class VOXnowIE(InfoExtractor):
    """Information Extractor for VOX NOW"""
    _VALID_URL = r'''(?x)
                        (?:https?://)?
                        (?P<url>
                            (?P<domain>
                               (?:www\.)?voxnow\.de
			    )
                            /+[a-zA-Z0-9-]+/[a-zA-Z0-9-]+\.php\?
                            (?:container_id|film_id)=(?P<video_id>[0-9]+)&
                            player=1(?:&season=[0-9]+)?(?:&.*)?
                        )'''

    _TEST = {
            'url': 'http://www.voxnow.de/der-hundeprofi/bulldogge-bruno-schaeferhuendin-mona.php?container_id=136867&player=1&season=6',
            'info_dict': {
                'id': '136867',
                'ext': 'mp4',
                'title': "Der Hundeprofi - Bulldogge 'Bruno' / Schäferhündin 'Mona'",
                'description': 'md5:eb5b500f3e97c476614a0c1989841060',
                'upload_date': '20150509',
                'duration': 3077,
            },
            'params': {
                'skip_download': True,
            },
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_page_url = 'http://%s/' % mobj.group('domain')
        video_id = mobj.group('video_id')

        webpage = self._download_webpage('http://' + mobj.group('url'), video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        upload_date = unified_strdate(self._html_search_meta('uploadDate', webpage, 'upload date'))

        mobj = re.search(r'<meta itemprop="duration" content="PT(?P<seconds>\d+)S" />', webpage)
        duration = int(mobj.group('seconds')) if mobj else None

        playerdata_url = self._html_search_regex(
            r"'playerdata': '(?P<playerdata_url>[^']+)'", webpage, 'playerdata_url')

        playerdata = self._download_xml(playerdata_url, video_id, 'Downloading player data XML')

        filename = playerdata.find('./playlist/videoinfo/filename').text
        manifest = self._download_xml(filename, video_id, 'Downloading manifest')

        formats = []
        for media in manifest.findall('{http://ns.adobe.com/f4m/2.0}media'):
            fmt = {
                'url': media.attrib['href'].replace('hds', 'hls').replace('f4m', 'm3u8'),
                'ext': 'mp4',
                'format_id': 'hls',
            }
            formats.append(fmt)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
        }
