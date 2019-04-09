# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .youtube import YoutubeIE
from .vimeo import VimeoIE
from ..utils import ExtractorError


class AmaraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?amara\.org/(?:\w+/)?videos/(?P<id>\w+).*'
    _TEST = {
        'url': 'https://amara.org/en/videos/jVx79ZKGK1ky/info/why-jury-trials-are-becoming-less-common/?tab=video',
        'md5': 'ea10daf2b6154b8c1ecf9922aca5e8ae',
        'info_dict': {
            'id': 'jVx79ZKGK1ky',
            'ext': 'mp4',
            'title': 'Why jury trials are becoming less common',
            'description': 'A new analysis of federal court cases published last week by The New York Times shows that jury trials are becoming increasingly less common. In 1997, 3,200 out of 63,000 federal defendants were convicted in jury trials. But by 2015, even as the number of defendants grew to 81,000, jury convictions dropped to 1,650. Benjamin Weiser of The New York Times joins William Brangham from Maine.',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': {
                'en': [
                    {'ext': 'vtt', 'url': 'https://amara.org/api/videos/jVx79ZKGK1ky/languages/en/subtitles/?format=json&format=vtt'},
                    {'ext': 'srt', 'url': 'https://amara.org/api/videos/jVx79ZKGK1ky/languages/en/subtitles/?format=json&format=srt'}
                ]
            }
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._download_json('https://amara.org/api/videos/%s/?extra=player_urls&format=json' % video_id, video_id)

        video_type = meta.get('video_type')
        video_url = meta.get('player_urls')[0]

        if video_type == 'Y':
            IE = YoutubeIE
        elif video_type == 'V':
            IE = VimeoIE
        else:
            raise ExtractorError('Could not find extractor for Amara video type %s.' % video_type)

        ie_info = IE(downloader=self._downloader).extract(video_url)

        subtitles = ie_info.get('subtitles', {}).copy()
        subtitles.update(dict(map(lambda language: [
            language['code'],
            [
                {
                    'ext': 'vtt',
                    'url': '%s&format=vtt' % language['subtitles_uri']
                }, {
                    'ext': 'srt',
                    'url': '%s&format=srt' % language['subtitles_uri']
                },
            ] + ie_info.get('subtitles', {}).get(language['code'], [])
        ], meta.get('languages', []))))

        return {
            'id': video_id,
            'title': meta.get('title') or ie_info.get('title'),
            'description': meta.get('description') or ie_info.get('description'),
            'thumbnail': meta.get('thumbnail') or ie_info.get('thumbnail'),
            'formats': ie_info.get('formats'),
            'subtitles': subtitles
        }
