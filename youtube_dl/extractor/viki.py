import re

from ..utils import (
    ExtractorError,
    unescapeHTML,
    unified_strdate,
)
from .subtitles import SubtitlesInfoExtractor


class VikiIE(SubtitlesInfoExtractor):
    IE_NAME = u'viki'

    _VALID_URL = r'^https?://(?:www\.)?viki\.com/videos/(?P<id>[0-9]+v)'
    _TEST = {
        u'url': u'http://www.viki.com/videos/1023585v-heirs-episode-14',
        u'file': u'1023585v.mp4',
        u'md5': u'a21454021c2646f5433514177e2caa5f',
        u'info_dict': {
            u'title': u'Heirs Episode 14',
            u'uploader': u'SBS',
            u'description': u'md5:c4b17b9626dd4b143dcc4d855ba3474e',
            u'upload_date': u'20131121',
            u'age_limit': 13,
        },
        u'skip': u'Blocked in the US',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

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
            u'rating information', default='').strip()
        RATINGS = {
            'G': 0,
            'PG': 10,
            'PG-13': 13,
            'R': 16,
            'NC': 18,
        }
        age_limit = RATINGS.get(rating_str)

        info_url = 'http://www.viki.com/player5_fragment/%s?action=show&controller=videos' % video_id
        info_webpage = self._download_webpage(
            info_url, video_id, note=u'Downloading info page')
        if re.match(r'\s*<div\s+class="video-error', info_webpage):
            raise ExtractorError(
                u'Video %s is blocked from your location.' % video_id,
                expected=True)
        video_url = self._html_search_regex(
            r'<source[^>]+src="([^"]+)"', info_webpage, u'video URL')

        upload_date_str = self._html_search_regex(
            r'"created_at":"([^"]+)"', info_webpage, u'upload date')
        upload_date = (
            unified_strdate(upload_date_str)
            if upload_date_str is not None
            else None
        )

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, info_webpage)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, info_webpage)
            return

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

    def _get_available_subtitles(self, video_id, info_webpage):
        res = {}
        for sturl_html in re.findall(r'<track src="([^"]+)"/>', info_webpage):
            sturl = unescapeHTML(sturl_html)
            m = re.search(r'/(?P<lang>[a-z]+)\.vtt', sturl)
            if not m:
                continue
            res[m.group('lang')] = sturl
        return res
