from __future__ import unicode_literals

import re

from .subtitles import SubtitlesInfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
    compat_urllib_parse,
)


class RaiIE(SubtitlesInfoExtractor):
    _VALID_URL = r'(?P<url>http://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it)/dl/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html)'
    _TESTS = [
        {
            'url': 'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-cb27157f-9dd0-4aee-b788-b1f67643a391.html',
            'md5': 'c064c0b2d09c278fb293116ef5d0a32d',
            'info_dict': {
                'id': 'cb27157f-9dd0-4aee-b788-b1f67643a391',
                'ext': 'mp4',
                'title': 'Report del 07/04/2014',
                'description': 'md5:f27c544694cacb46a078db84ec35d2d9',
                'upload_date': '20140407',
                'duration': 6160,
            }
        },
        {
            'url': 'http://www.raisport.rai.it/dl/raiSport/media/rassegna-stampa-04a9f4bd-b563-40cf-82a6-aad3529cb4a9.html',
            'md5': '8bb9c151924ce241b74dd52ef29ceafa',
            'info_dict': {
                'id': '04a9f4bd-b563-40cf-82a6-aad3529cb4a9',
                'ext': 'mp4',
                'title': 'TG PRIMO TEMPO',
                'description': '',
                'upload_date': '20140612',
                'duration': 1758,
            },
            'skip': 'Error 404',
        },
        {
            'url': 'http://www.rainews.it/dl/rainews/media/state-of-the-net-Antonella-La-Carpia-regole-virali-7aafdea9-0e5d-49d5-88a6-7e65da67ae13.html',
            'md5': '35cf7c229f22eeef43e48b5cf923bef0',
            'info_dict': {
                'id': '7aafdea9-0e5d-49d5-88a6-7e65da67ae13',
                'ext': 'mp4',
                'title': 'State of the Net, Antonella La Carpia: regole virali',
                'description': 'md5:b0ba04a324126903e3da7763272ae63c',
                'upload_date': '20140613',
            },
            'skip': 'Error 404',
        },
        {
            'url': 'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-b4a49761-e0cc-4b14-8736-2729f6f73132-tg2.html',
            'md5': '35694f062977fe6619943f08ed935730',
            'info_dict': {
                'id': 'b4a49761-e0cc-4b14-8736-2729f6f73132',
                'ext': 'mp4',
                'title': 'Alluvione in Sardegna e dissesto idrogeologico',
                'description': 'Edizione delle ore 20:30 ',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        media = self._download_json('%s?json' % mobj.group('url'), video_id, 'Downloading video JSON')

        title = media.get('name')
        description = media.get('desc')
        thumbnail = media.get('image_300') or media.get('image_medium') or media.get('image')
        duration = parse_duration(media.get('length'))
        uploader = media.get('author')
        upload_date = unified_strdate(media.get('date'))

        formats = []

        for format_id in ['wmv', 'm3u8', 'mediaUri', 'h264']:
            media_url = media.get(format_id)
            if not media_url:
                continue
            formats.append({
                'url': media_url,
                'format_id': format_id,
                'ext': 'mp4',
            })

        if self._downloader.params.get('listsubtitles', False):
            page = self._download_webpage(url, video_id)
            self._list_available_subtitles(video_id, page)
            return

        subtitles = {}
        if self._have_to_download_any_subtitles:
            page = self._download_webpage(url, video_id)
            subtitles = self.extract_subtitles(video_id, page)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }

    def _get_available_subtitles(self, video_id, webpage):
        subtitles = {}
        m = re.search(r'<meta name="closedcaption" content="(?P<captions>[^"]+)"', webpage)
        if m:
            captions = m.group('captions')
            STL_EXT = '.stl'
            SRT_EXT = '.srt'
            if captions.endswith(STL_EXT):
                captions = captions[:-len(STL_EXT)] + SRT_EXT
            subtitles['it'] = 'http://www.rai.tv%s' % compat_urllib_parse.quote(captions)
        return subtitles
