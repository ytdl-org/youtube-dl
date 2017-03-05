# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
    smuggle_url,
)


class TVAIE(InfoExtractor):
    _VALID_URL = r'https?://videos\.tva\.ca/episode/(?P<id>\d+)'
    _TEST = {
        'url': 'http://videos.tva.ca/episode/85538',
        'info_dict': {
            'id': '85538',
            'ext': 'mp4',
            'title': 'Épisode du 25 janvier 2017',
            'description': 'md5:e9e7fb5532ab37984d2dc87229cadf98',
            'upload_date': '20170126',
            'timestamp': 1485442329,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            "https://d18jmrhziuoi7p.cloudfront.net/isl/api/v1/dataservice/Items('%s')" % video_id,
            video_id, query={
                '$expand': 'Metadata,CustomId',
                '$select': 'Metadata,Id,Title,ShortDescription,LongDescription,CreatedDate,CustomId,AverageUserRating,Categories,ShowName',
                '$format': 'json',
            })
        metadata = video_data.get('Metadata', {})

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': video_data['Title'],
            'url': smuggle_url('ooyala:' + video_data['CustomId'], {'supportedformats': 'm3u8,hds'}),
            'description': video_data.get('LongDescription') or video_data.get('ShortDescription'),
            'series': video_data.get('ShowName'),
            'episode': metadata.get('EpisodeTitle'),
            'episode_number': int_or_none(metadata.get('EpisodeNumber')),
            'categories': video_data.get('Categories'),
            'average_rating': video_data.get('AverageUserRating'),
            'timestamp': parse_iso8601(video_data.get('CreatedDate')),
            'ie_key': 'Ooyala',
        }
