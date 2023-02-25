# coding: utf-8
from __future__ import unicode_literals

from ..utils import (
    compat_str,
    ExtractorError,
    int_or_none,
    strip_or_none,
    try_get,
    url_or_none
)
from .common import InfoExtractor


class BellesaIE(InfoExtractor):
    _VALID_URL = r'''https?://www\.bellesa\.co/videos/(?P<id>[0-9]+)/'''
    _TESTS = [{
        'url': 'https://www.bellesa.co/videos/2189/my-first-time-kissing-women',
        'md5': '543b002f4d1e5b4a0dde243f4a43fd28',
        'info_dict': {
            'id': '2189',
            'ext': 'mp4',
            'title': 'My First Time Kissing Women',
            'thumbnail': 'https://c.bellesa.co/dkvdbifey/image/upload/v1599024046/video_upload/2189cover.jpg',
            'description': 'md5:69eea8a4ee31d42d6fd6302ad9e09ab2',
            'creator': 'Bellesa Films',
            'upload_date': '20191216',
            'timestamp': 1576539206,
            'duration': 721,
            'tags': 'mincount:15',
            'categories': ['Girl on Girl', 'Story'],
            'age_limit': 18,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.bellesa.co/videos/%s/' % video_id, video_id)

        # videos on this page are embedded into a container called VideoCard - if there is
        # nothing on the page referencing a VideoCard we cannot extract the information and
        # thus need to raise an error
        # the VideoCard container is not specific html element but rather only mentioned in
        # CSS styles; hence we cannot use get_element_by_id and the like to find our info
        # but instead just quickly check whether or not we have a page with a video
        if 'VideoCard' not in webpage:
            raise ExtractorError('[%s] %s: page does not contain a VideoCard', self.IE_NAME, video_id, expected=True)

        initial_data_raw = self._search_regex(r'(?s)window\s*\.\s*__INITIAL_DATA__\s*=\s*(\{.+?\})\s*;\s*</script>', webpage, 'initial_data')

        initial_data = self._parse_json(initial_data_raw, video_id)
        if not initial_data:
            raise ExtractorError('[%s] %s: cannot decode initial data', self.IE_NAME, video_id, expected=True)

        video = try_get(initial_data, lambda x: x['video'])
        if not video:
            raise ExtractorError('[%s] %s: initial data malformed' % self.IE_NAME, video_id, expected=True)

        resolutions = video.get('resolutions')
        source = video.get('source')

        if not resolutions or not source:
            raise ExtractorError('[%s] %s: cannot extract playlist information from meta data' % self.IE_NAME, video_id, expected=True)

        m3u8_url = 'https://s.bellesa.co/hls/v/%s/,%s,.mp4.urlset/master.m3u8' % (source, resolutions)

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls',
            fatal=False)

        if not formats:
            raise ExtractorError('[%s] %s: cannot extract formats from m3u8 file', self.IE_NAME, video_id, expected=True)

        self._sort_formats(formats)

        # get from video meta data first
        title = strip_or_none(video.get('title'))
        if not title:
            # fallback to og:title, which needs some treatment
            title = self._og_search_title(webpage)
            if title:
                title = title.split('|')[0].strip()

        tags = list(filter(None, map(lambda s: s.strip(), (video.get('tags') or '').split(','))))
        categories = list(filter(None, map(lambda d: strip_or_none(d['name']), (video.get('categories') or []))))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': url_or_none(video.get('image')),
            'description': strip_or_none(video.get('description')) or None,
            'creator': try_get(video, lambda x: x['content_provider'][0]['name'].strip(), compat_str),
            'timestamp': int_or_none(video.get('posted_on')),
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('views')),
            'tags': tags or None,
            'categories': categories or None,
            'age_limit': 18,
            'formats': formats,
        }
