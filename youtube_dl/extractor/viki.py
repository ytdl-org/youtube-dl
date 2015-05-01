from __future__ import unicode_literals

import re

from ..compat import (
    compat_urlparse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    unescapeHTML,
    unified_strdate,
    US_RATINGS,
)
from .common import InfoExtractor


class VikiIE(InfoExtractor):
    IE_NAME = 'viki'

    # iPad2
    _USER_AGENT = 'Mozilla/5.0(iPad; U; CPU OS 4_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F191 Safari/6533.18.5'

    _VALID_URL = r'^https?://(?:www\.)?viki\.com/videos/(?P<id>[0-9]+v)'
    _TESTS = [{
        'url': 'http://www.viki.com/videos/1023585v-heirs-episode-14',
        'info_dict': {
            'id': '1023585v',
            'ext': 'mp4',
            'title': 'Heirs Episode 14',
            'uploader': 'SBS',
            'description': 'md5:c4b17b9626dd4b143dcc4d855ba3474e',
            'upload_date': '20131121',
            'age_limit': 13,
        },
        'skip': 'Blocked in the US',
    }, {
        'url': 'http://www.viki.com/videos/1067139v-the-avengers-age-of-ultron-press-conference',
        'md5': 'ca6493e6f0a6ec07da9aa8d6304b4b2c',
        'info_dict': {
            'id': '1067139v',
            'ext': 'mp4',
            'description': 'md5:d70b2f9428f5488321bfe1db10d612ea',
            'upload_date': '20150430',
            'title': '\'The Avengers: Age of Ultron\' Press Conference',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        uploader_m = re.search(
            r'<strong>Broadcast Network: </strong>\s*([^<]*)<', webpage)
        if uploader_m is None:
            uploader = None
        else:
            uploader = uploader_m.group(1).strip()

        rating_str = self._html_search_regex(
            r'<strong>Rating: </strong>\s*([^<]*)<', webpage,
            'rating information', default='').strip()
        age_limit = US_RATINGS.get(rating_str)

        req = compat_urllib_request.Request(
            'http://www.viki.com/player5_fragment/%s?action=show&controller=videos' % video_id)
        req.add_header('User-Agent', self._USER_AGENT)
        info_webpage = self._download_webpage(
            req, video_id, note='Downloading info page')
        if re.match(r'\s*<div\s+class="video-error', info_webpage):
            raise ExtractorError(
                'Video %s is blocked from your location.' % video_id,
                expected=True)
        video_url = self._html_search_regex(
            r'<source[^>]+src="([^"]+)"', info_webpage, 'video URL')

        upload_date_str = self._html_search_regex(
            r'"created_at":"([^"]+)"', info_webpage, 'upload date')
        upload_date = (
            unified_strdate(upload_date_str)
            if upload_date_str is not None
            else None
        )

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, info_webpage)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'description': description,
            'thumbnail': thumbnail,
            'age_limit': age_limit,
            'uploader': uploader,
            'subtitles': video_subtitles,
            'upload_date': upload_date,
        }

    def _get_subtitles(self, video_id, info_webpage):
        res = {}
        for sturl_html in re.findall(r'<track src="([^"]+)"', info_webpage):
            sturl = unescapeHTML(sturl_html)
            m = re.search(r'/(?P<lang>[a-z]+)\.vtt', sturl)
            if not m:
                continue
            res[m.group('lang')] = [{
                'url': compat_urlparse.urljoin('http://www.viki.com', sturl),
                'ext': 'vtt',
            }]
        return res
