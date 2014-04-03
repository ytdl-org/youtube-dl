# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_parse_qs,
    compat_urlparse,
)


class FranceCultureIE(InfoExtractor):
    _VALID_URL = r'(?P<baseurl>http://(?:www\.)?franceculture\.fr/)player/reecouter\?play=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.franceculture.fr/player/reecouter?play=4795174',
        'info_dict': {
            'id': '4795174',
            'ext': 'mp3',
            'title': 'Rendez-vous au pays des geeks',
            'vcodec': 'none',
            'uploader': 'Colette Fellous',
            'upload_date': '20140301',
            'duration': 3601,
            'thumbnail': r're:^http://www\.franceculture\.fr/.*/images/player/Carnet-nomade\.jpg$',
            'description': 'Avec :Jean-Baptiste Péretié pour son documentaire sur Arte "La revanche des « geeks », une enquête menée aux Etats-Unis dans la S ...',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        baseurl = mobj.group('baseurl')

        webpage = self._download_webpage(url, video_id)
        params_code = self._search_regex(
            r"<param name='movie' value='/sites/all/modules/rf/rf_player/swf/loader.swf\?([^']+)' />",
            webpage, 'parameter code')
        params = compat_parse_qs(params_code)
        video_url = compat_urlparse.urljoin(baseurl, params['urlAOD'][0])

        title = self._html_search_regex(
            r'<h1 class="title[^"]+">(.+?)</h1>', webpage, 'title')
        uploader = self._html_search_regex(
            r'(?s)<div id="emission".*?<span class="author">(.*?)</span>',
            webpage, 'uploader', fatal=False)
        thumbnail_part = self._html_search_regex(
            r'(?s)<div id="emission".*?<img src="([^"]+)"', webpage,
            'thumbnail', fatal=False)
        if thumbnail_part is None:
            thumbnail = None
        else:
            thumbnail = compat_urlparse.urljoin(baseurl, thumbnail_part)
        description = self._html_search_regex(
            r'(?s)<p class="desc">(.*?)</p>', webpage, 'description')

        info = json.loads(params['infoData'][0])[0]
        duration = info.get('media_length')
        upload_date_candidate = info.get('media_section5')
        upload_date = (
            upload_date_candidate
            if (upload_date_candidate is not None and
                re.match(r'[0-9]{8}$', upload_date_candidate))
            else None)

        return {
            'id': video_id,
            'url': video_url,
            'vcodec': 'none' if video_url.lower().endswith('.mp3') else None,
            'duration': duration,
            'uploader': uploader,
            'upload_date': upload_date,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
        }
