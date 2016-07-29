# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_HTTPError,
)
from ..utils import (
    ExtractorError,
    HEADRequest,
    remove_end,
)


class CloudyIE(InfoExtractor):
    _IE_DESC = 'cloudy.ec'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?cloudy\.ec/
        (?:v/|embed\.php\?id=)
        (?P<id>[A-Za-z0-9]+)
        '''
    _EMBED_URL = 'http://www.cloudy.ec/embed.php?id=%s'
    _API_URL = 'http://www.cloudy.ec/api/player.api.php'
    _MAX_TRIES = 2
    _TEST = {
        'url': 'https://www.cloudy.ec/v/af511e2527aac',
        'md5': '5cb253ace826a42f35b4740539bedf07',
        'info_dict': {
            'id': 'af511e2527aac',
            'ext': 'flv',
            'title': 'Funny Cats and Animals Compilation june 2013',
        }
    }

    def _extract_video(self, video_id, file_key, error_url=None, try_num=0):

        if try_num > self._MAX_TRIES - 1:
            raise ExtractorError('Unable to extract video URL', expected=True)

        form = {
            'file': video_id,
            'key': file_key,
        }

        if error_url:
            form.update({
                'numOfErrors': try_num,
                'errorCode': '404',
                'errorUrl': error_url,
            })

        player_data = self._download_webpage(
            self._API_URL, video_id, 'Downloading player data', query=form)
        data = compat_parse_qs(player_data)

        try_num += 1

        if 'error' in data:
            raise ExtractorError(
                '%s error: %s' % (self.IE_NAME, ' '.join(data['error_msg'])),
                expected=True)

        title = data.get('title', [None])[0]
        if title:
            title = remove_end(title, '&asdasdas').strip()

        video_url = data.get('url', [None])[0]

        if video_url:
            try:
                self._request_webpage(HEADRequest(video_url), video_id, 'Checking video URL')
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code in [404, 410]:
                    self.report_warning('Invalid video URL, requesting another', video_id)
                    return self._extract_video(video_id, file_key, video_url, try_num)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = self._EMBED_URL % video_id
        webpage = self._download_webpage(url, video_id)

        file_key = self._search_regex(
            [r'key\s*:\s*"([^"]+)"', r'filekey\s*=\s*"([^"]+)"'],
            webpage, 'file_key')

        return self._extract_video(video_id, file_key)
