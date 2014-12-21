from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
)
from ..utils import (
    int_or_none,
    ExtractorError,
)


class VeohIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?veoh\.com/(?:watch|iphone/#_Watch)/(?P<id>(?:v|yapi-)[\da-zA-Z]+)'

    _TESTS = [
        {
            'url': 'http://www.veoh.com/watch/v56314296nk7Zdmz3',
            'md5': '620e68e6a3cff80086df3348426c9ca3',
            'info_dict': {
                'id': '56314296',
                'ext': 'mp4',
                'title': 'Straight Backs Are Stronger',
                'uploader': 'LUMOback',
                'description': 'At LUMOback, we believe straight backs are stronger.  The LUMOback Posture & Movement Sensor:  It gently vibrates when you slouch, inspiring improved posture and mobility.  Use the app to track your data and improve your posture over time. ',
            },
        },
        {
            'url': 'http://www.veoh.com/watch/v27701988pbTc4wzN?h1=Chile+workers+cover+up+to+avoid+skin+damage',
            'md5': '4a6ff84b87d536a6a71e6aa6c0ad07fa',
            'info_dict': {
                'id': '27701988',
                'ext': 'mp4',
                'title': 'Chile workers cover up to avoid skin damage',
                'description': 'md5:2bd151625a60a32822873efc246ba20d',
                'uploader': 'afp-news',
                'duration': 123,
            },
        },
        {
            'url': 'http://www.veoh.com/watch/v69525809F6Nc4frX',
            'md5': '4fde7b9e33577bab2f2f8f260e30e979',
            'note': 'Embedded ooyala video',
            'info_dict': {
                'id': '69525809',
                'ext': 'mp4',
                'title': 'Doctors Alter Plan For Preteen\'s Weight Loss Surgery',
                'description': 'md5:f5a11c51f8fb51d2315bca0937526891',
                'uploader': 'newsy-videos',
            },
            'skip': 'This video has been deleted.',
        },
    ]

    def _extract_formats(self, source):
        formats = []
        link = source.get('aowPermalink')
        if link:
            formats.append({
                'url': link,
                'ext': 'mp4',
                'format_id': 'aow',
            })
        link = source.get('fullPreviewHashLowPath')
        if link:
            formats.append({
                'url': link,
                'format_id': 'low',
            })
        link = source.get('fullPreviewHashHighPath')
        if link:
            formats.append({
                'url': link,
                'format_id': 'high',
            })
        return formats

    def _extract_video(self, source):
        return {
            'id': source.get('videoId'),
            'title': source.get('title'),
            'description': source.get('description'),
            'thumbnail': source.get('highResImage') or source.get('medResImage'),
            'uploader': source.get('username'),
            'duration': int_or_none(source.get('length')),
            'view_count': int_or_none(source.get('views')),
            'age_limit': 18 if source.get('isMature') == 'true' or source.get('isSexy') == 'true' else 0,
            'formats': self._extract_formats(source),
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        if video_id.startswith('v'):
            rsp = self._download_xml(
                r'http://www.veoh.com/api/findByPermalink?permalink=%s' % video_id, video_id, 'Downloading video XML')
            stat = rsp.get('stat')
            if stat == 'ok':
                return self._extract_video(rsp.find('./videoList/video'))
            elif stat == 'fail':
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, rsp.find('./errorList/error').get('errorMessage')), expected=True)

        webpage = self._download_webpage(url, video_id)
        age_limit = 0
        if 'class="adultwarning-container"' in webpage:
            self.report_age_confirmation()
            age_limit = 18
            request = compat_urllib_request.Request(url)
            request.add_header('Cookie', 'confirmedAdult=true')
            webpage = self._download_webpage(request, video_id)

        m_youtube = re.search(r'http://www\.youtube\.com/v/(.*?)(\&|"|\?)', webpage)
        if m_youtube is not None:
            youtube_id = m_youtube.group(1)
            self.to_screen('%s: detected Youtube video.' % video_id)
            return self.url_result(youtube_id, 'Youtube')

        info = json.loads(
            self._search_regex(r'videoDetailsJSON = \'({.*?})\';', webpage, 'info').replace('\\\'', '\''))

        video = self._extract_video(info)
        video['age_limit'] = age_limit

        return video
