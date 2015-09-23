# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from .theplatform import ThePlatformIE


class CNETIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cnet\.com/videos/(?P<id>[^/]+)/'
    _TESTS = [{
        'url': 'http://www.cnet.com/videos/hands-on-with-microsofts-windows-8-1-update/',
        'info_dict': {
            'id': '56f4ea68-bd21-4852-b08c-4de5b8354c60',
            'ext': 'mp4',
            'title': 'Hands-on with Microsoft Windows 8.1 Update',
            'description': 'The new update to the Windows 8 OS brings improved performance for mouse and keyboard users.',
            'uploader_id': '6085384d-619e-11e3-b231-14feb5ca9861',
            'uploader': 'Sarah Mitroff',
        },
    }, {
        'url': 'http://www.cnet.com/videos/whiny-pothole-tweets-at-local-government-when-hit-by-cars-tomorrow-daily-187/',
        'info_dict': {
            'id': '56527b93-d25d-44e3-b738-f989ce2e49ba',
            'ext': 'mp4',
            'description': 'Khail and Ashley wonder what other civic woes can be solved by self-tweeting objects, investigate a new kind of VR camera and watch an origami robot self-assemble, walk, climb, dig and dissolve. #TDPothole',
            'uploader_id': 'b163284d-6b73-44fc-b3e6-3da66c392d40',
            'uploader': 'Ashley Esqueda',
            'title': 'Whiny potholes tweet at local government when hit by cars (Tomorrow Daily 187)',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        data_json = self._html_search_regex(
            r"<div class=\"videoPlayer\"\s+.*?data-cnet-video-uvp-options='([^']+)'",
            webpage, 'data json')
        data = json.loads(data_json)
        vdata = data['videos'][0]

        video_id = vdata['id']
        title = vdata['title']
        author = vdata.get('author')
        if author:
            uploader = '%s %s' % (author['firstName'], author['lastName'])
            uploader_id = author.get('id')
        else:
            uploader = None
            uploader_id = None

        mpx_account = data['config']['uvpConfig']['default']['mpx_account']
        tp = ThePlatformIE(self._downloader)
        formats = []
        subtitles = {}
        description = vdata.get('description')

        for vid in vdata['files'].values():
            result = tp.extract(('http://link.theplatform.com/s/%s/%s' % (mpx_account, vid)))
            formats.extend(result['formats'])
            subtitles = self._merge_subtitles(subtitles, result['subtitles'])
            description = description or result.get('description')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'subtitles': subtitles,
            'formats': formats,
        }
