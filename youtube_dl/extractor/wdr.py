from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    compat_urlparse,
    determine_ext,
)


class WDRIE(InfoExtractor):
    _PLAYER_REGEX = '-(?:video|audio)player(?:_size-[LMS])?'
    _VALID_URL = r'(?P<url>https?://www\d?\.(?:wdr\d?|funkhauseuropa)\.de/)(?P<id>.+?)(?P<player>%s)?\.html' % _PLAYER_REGEX

    _TESTS = [
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/servicezeit/videoservicezeit560-videoplayer_size-L.html',
            'info_dict': {
                'id': 'mdb-362427',
                'ext': 'flv',
                'title': 'Servicezeit',
                'description': 'md5:c8f43e5e815eeb54d0b96df2fba906cb',
                'upload_date': '20140310',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www1.wdr.de/themen/av/videomargaspiegelisttot101-videoplayer.html',
            'info_dict': {
                'id': 'mdb-363194',
                'ext': 'flv',
                'title': 'Marga Spiegel ist tot',
                'description': 'md5:2309992a6716c347891c045be50992e4',
                'upload_date': '20140311',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www1.wdr.de/themen/kultur/audioerlebtegeschichtenmargaspiegel100-audioplayer.html',
            'md5': '83e9e8fefad36f357278759870805898',
            'info_dict': {
                'id': 'mdb-194332',
                'ext': 'mp3',
                'title': 'Erlebte Geschichten: Marga Spiegel (29.11.2009)',
                'description': 'md5:2309992a6716c347891c045be50992e4',
                'upload_date': '20091129',
            },
        },
        {
            'url': 'http://www.funkhauseuropa.de/av/audiogrenzenlosleckerbaklava101-audioplayer.html',
            'md5': 'cfff440d4ee64114083ac44676df5d15',
            'info_dict': {
                'id': 'mdb-363068',
                'ext': 'mp3',
                'title': 'Grenzenlos lecker - Baklava',
                'description': 'md5:7b29e97e10dfb6e265238b32fa35b23a',
                'upload_date': '20140311',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_url = mobj.group('url')
        page_id = mobj.group('id')

        webpage = self._download_webpage(url, page_id)

        if mobj.group('player') is None:
            entries = [
                self.url_result(page_url + href, 'WDR')
                for href in re.findall(r'<a href="/?(.+?%s\.html)" rel="nofollow"' % self._PLAYER_REGEX, webpage)
            ]
            return self.playlist_result(entries, page_id)

        flashvars = compat_urlparse.parse_qs(
            self._html_search_regex(r'<param name="flashvars" value="([^"]+)"', webpage, 'flashvars'))

        page_id = flashvars['trackerClipId'][0]
        video_url = flashvars['dslSrc'][0]
        title = flashvars['trackerClipTitle'][0]
        thumbnail = flashvars['startPicture'][0] if 'startPicture' in flashvars else None

        if 'trackerClipAirTime' in flashvars:
            upload_date = flashvars['trackerClipAirTime'][0]
        else:
            upload_date = self._html_search_meta('DC.Date', webpage, 'upload date')

        if upload_date:
            upload_date = unified_strdate(upload_date)

        if video_url.endswith('.f4m'):
            video_url += '?hdcore=3.2.0&plugin=aasp-3.2.0.77.18'
            ext = 'flv'
        else:
            ext = determine_ext(video_url)

        description = self._html_search_meta('Description', webpage, 'description')

        return {
            'id': page_id,
            'url': video_url,
            'ext': ext,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
        }