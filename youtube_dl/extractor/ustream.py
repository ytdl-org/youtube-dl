from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
)


class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/(?P<type>recorded|embed|embed/recorded)/(?P<id>\d+)'
    IE_NAME = 'ustream'
    _TESTS = [{
        'url': 'http://www.ustream.tv/recorded/20274954',
        'md5': '088f151799e8f572f84eb62f17d73e5c',
        'info_dict': {
            'id': '20274954',
            'ext': 'flv',
            'title': 'Young Americans for Liberty February 7, 2012 2:28 AM',
            'description': 'Young Americans for Liberty February 7, 2012 2:28 AM',
            'timestamp': 1328577035,
            'upload_date': '20120207',
            'uploader': 'yaliberty',
            'uploader_id': '6780869',
        },
    }, {
        # From http://sportscanada.tv/canadagames/index.php/week2/figure-skating/444
        # Title and uploader available only from params JSON
        'url': 'http://www.ustream.tv/embed/recorded/59307601?ub=ff0000&lc=ff0000&oc=ffffff&uc=ffffff&v=3&wmode=direct',
        'md5': '5a2abf40babeac9812ed20ae12d34e10',
        'info_dict': {
            'id': '59307601',
            'ext': 'flv',
            'title': '-CG11- Canada Games Figure Skating',
            'uploader': 'sportscanadatv',
        },
        'skip': 'This Pro Broadcaster has chosen to remove this video from the ustream.tv site.',
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        # some sites use this embed format (see: http://github.com/rg3/youtube-dl/issues/2990)
        if m.group('type') == 'embed/recorded':
            video_id = m.group('id')
            desktop_url = 'http://www.ustream.tv/recorded/' + video_id
            return self.url_result(desktop_url, 'Ustream')
        if m.group('type') == 'embed':
            video_id = m.group('id')
            webpage = self._download_webpage(url, video_id)
            desktop_video_id = self._html_search_regex(
                r'ContentVideoIds=\["([^"]*?)"\]', webpage, 'desktop_video_id')
            desktop_url = 'http://www.ustream.tv/recorded/' + desktop_video_id
            return self.url_result(desktop_url, 'Ustream')

        params = self._download_json(
            'https://api.ustream.tv/videos/%s.json' % video_id, video_id)

        error = params.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error), expected=True)

        video = params['video']

        title = video['title']
        filesize = float_or_none(video.get('file_size'))

        formats = [{
            'id': video_id,
            'url': video_url,
            'ext': format_id,
            'filesize': filesize,
        } for format_id, video_url in video['media_urls'].items()]
        self._sort_formats(formats)

        description = video.get('description')
        timestamp = int_or_none(video.get('created_at'))
        duration = float_or_none(video.get('length'))
        view_count = int_or_none(video.get('views'))

        uploader = video.get('owner', {}).get('username')
        uploader_id = video.get('owner', {}).get('id')

        thumbnails = [{
            'id': thumbnail_id,
            'url': thumbnail_url,
        } for thumbnail_id, thumbnail_url in video.get('thumbnail', {}).items()]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
        }


class UstreamChannelIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/channel/(?P<slug>.+)'
    IE_NAME = 'ustream:channel'
    _TEST = {
        'url': 'http://www.ustream.tv/channel/channeljapan',
        'info_dict': {
            'id': '10874166',
        },
        'playlist_mincount': 17,
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        display_id = m.group('slug')
        webpage = self._download_webpage(url, display_id)
        channel_id = self._html_search_meta('ustream:channel_id', webpage)

        BASE = 'http://www.ustream.tv'
        next_url = '/ajax/socialstream/videos/%s/1.json' % channel_id
        video_ids = []
        while next_url:
            reply = self._download_json(
                compat_urlparse.urljoin(BASE, next_url), display_id,
                note='Downloading video information (next: %d)' % (len(video_ids) + 1))
            video_ids.extend(re.findall(r'data-content-id="(\d.*)"', reply['data']))
            next_url = reply['nextUrl']

        entries = [
            self.url_result('http://www.ustream.tv/recorded/' + vid, 'Ustream')
            for vid in video_ids]
        return {
            '_type': 'playlist',
            'id': channel_id,
            'display_id': display_id,
            'entries': entries,
        }
