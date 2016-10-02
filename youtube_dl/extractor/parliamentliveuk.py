from __future__ import unicode_literals

from .common import InfoExtractor


class ParliamentLiveUKIE(InfoExtractor):
    IE_NAME = 'parliamentlive.tv'
    IE_DESC = 'UK parliament videos'
    _VALID_URL = r'https?://(?:www\.)?parliamentlive\.tv/Event/Index/(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'

    _TEST = {
        'url': 'http://parliamentlive.tv/Event/Index/c1e9d44d-fd6c-4263-b50f-97ed26cc998b',
        'info_dict': {
            'id': 'c1e9d44d-fd6c-4263-b50f-97ed26cc998b',
            'ext': 'mp4',
            'title': 'Home Affairs Committee',
            'uploader_id': 'FFMPEG-01',
            'timestamp': 1422696664,
            'upload_date': '20150131',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://vodplayer.parliamentlive.tv/?mid=' + video_id, video_id)
        widget_config = self._parse_json(self._search_regex(
            r'kWidgetConfig\s*=\s*({.+});',
            webpage, 'kaltura widget config'), video_id)
        kaltura_url = 'kaltura:%s:%s' % (widget_config['wid'][1:], widget_config['entry_id'])
        event_title = self._download_json(
            'http://parliamentlive.tv/Event/GetShareVideo/' + video_id, video_id)['event']['title']
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': event_title,
            'description': '',
            'url': kaltura_url,
            'ie_key': 'Kaltura',
        }
