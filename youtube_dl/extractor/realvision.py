# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from datetime import datetime

from ..utils import (
    try_get,
    int_or_none,
    float_or_none,
    ExtractorError,
)


class RealVisionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?realvision\.com/shows/.*?/videos/.*?'

    _TEST = {
        'url': 'https://www.realvision.com/shows/the-interview/videos/how-coronavirus-exposed-the-shaky-foundation',
        'info_dict': {
            'uploader_id': '3117927975001',
            'id': '6145338821001',
            'ext': 'mp4',
            'title': 'How Coronavirus Exposed the "Shaky Foundation"',
            'description': 'What happens when an upheaval so massive forces financial markets, governments, and society to rethink how our systems work? Michael Krieger, author of the Liberty Blitzkrieg, joins Real Vision to explain what coronavirus and the response to the outbreak has revealed about the condition of American systems – from financial markets to the health care system. Tracing the story of financial markets and societal trends over the past two decades, Krieger outlines how our systems have been pushed to the brink – focusing on emergency policy responses and the everything bubble. He also provides viewers with potential solutions to the systemic decay that has been brought to the forefront by the coronavirus outbreak.',
            'thumbnail': 'https://www.realvision.com:443/rv/media/Video/d9b77910037f458497a56654165e459e/thumbnail',
            'timestamp': 1585371600,
            'upload_date': '20200312',
            'release_date': '20200328',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['BrightcoveNew'],
    }

    REALVISION_URL_TEMPLATE = 'https://www.realvision.com/rv/api/videos/%s?include=videoassets,viewer'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/3117927975001/default_default/index.html?videoId=%s'

    def strdate_from_timestamp(timestamp):
        return datetime.utcfromtimestamp(timestamp).strftime('%Y%m%d') if timestamp else None

    def _real_extract(self, url):
        webpage = self._download_webpage(url, url)
        rv_id = self._search_regex(
            r'<meta name="twitter:image" content="https://ichef.realvision.com/(.+?)/hero" />',
            webpage, 'rv_id', fatal=True)
        meta = self._download_json(self.REALVISION_URL_TEMPLATE % (rv_id), rv_id)

        included = meta.get('included')
        if not included:
            raise ExtractorError('No assets for %s; missing cookiefile with paid subscription?' % rv_id, expected=True)

        bc_id = try_get(included[0], lambda x: x['attributes']['videoassets_brightcove_id'])
        if not bc_id:
            raise ExtractorError('No Brightcove assets for %s.' % rv_id, expected=True)

        filmed_timestamp = int_or_none(try_get(meta, lambda x: x['data']['attributes']['video_filmed_on']), scale=1000)
        published_timestamp = int_or_none(try_get(meta, lambda x: x['data']['attributes']['video_published_on']), scale=1000)

        return {
            '_type': 'url_transparent',
            'url': self.BRIGHTCOVE_URL_TEMPLATE % (bc_id),
            'title': try_get(meta, lambda x: x['data']['attributes']['video_title']),
            'description': try_get(meta, lambda x: x['data']['attributes']['video_description']),
            'thumbnail': try_get(meta, lambda x: x['data']['links']['thumbnail']),
            'timestamp': published_timestamp,
            'upload_date': RealVisionIE.strdate_from_timestamp(filmed_timestamp),
            'release_date': RealVisionIE.strdate_from_timestamp(published_timestamp),
            'like_count': int_or_none(try_get(meta, lambda x: x['data']['attributes']['video_likes_count'])),
            'dislike_count': int_or_none(try_get(meta, lambda x: x['data']['attributes']['video_dislikes_count'])),
            'average_rating': float_or_none(try_get(meta, lambda x: x['data']['attributes']['video_rating'])),
            'ie_key': 'BrightcoveNew',
        }
