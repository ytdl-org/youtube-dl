# coding: utf-8
from __future__ import unicode_literals

import re
from datetime import datetime

from .common import InfoExtractor
from ..utils import (
    clean_html,
    get_element_by_id,
    int_or_none,
    sanitize_url,
)


class Go90IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?go90\.com/profiles/va_(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.go90.com/profiles/va_07d47f43a7b04eb5b693252f2bd1086b',
        'info_dict': {
            'id': '07d47f43a7b04eb5b693252f2bd1086b',
            'ext': 'mp4',
            'title': 't@gged S01E01 #shotgun',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:1ebcc7a686d93456a822d435d2ac7719',
            'uploader_id': '98ac1613c7624a8387596b5d5e441064',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)


        # scrape data from webpage
        self.to_screen("Scrape data from webpage")

        series_title = clean_html(get_element_by_id('series-title', webpage))
        self.to_screen("Series Title: " + series_title)

        episode_info = clean_html(get_element_by_id('episode-title', webpage))

        season_number = None
        episode_number = None
        episode_title = None

        episode_match = re.match(
            r'S(?P<season_number>\d+):E(?P<episode_number>\d+)\s+(?P<episode_title>.*)',
            episode_info)
        if episode_match is not None:
            season_number, episode_number, episode_title = episode_match.groups()
            self.to_screen("Season: " + season_number)
            self.to_screen("Episode Number: " + episode_number)
            self.to_screen("Episode Title: " + episode_title)

        video_title = series_title
        if episode_match is not None:
            video_title = '{} S{:02d}E{:02d} {}'.format(
                series_title, int_or_none(season_number), int_or_none(episode_number), episode_title)
        self.to_screen("Title: " + video_title)

        video_description = self._og_search_description(webpage)

        release_date = None
        air_date = clean_html(get_element_by_id('asset-air-date', webpage))
        if air_date:
            self.to_screen("Air Date: " + air_date)
            release_datetime = datetime.strptime(air_date, '%b %d, %Y')
            release_date = release_datetime.strftime('%Y%m%d')


        # retrieve upLynk url
        video_api = "https://www.go90.com/api/metadata/video/" + video_id
        video_api_data = self._download_json(video_api, video_id)
        uplynk_preplay_url = sanitize_url(video_api_data['url'])


        return {
            '_type': 'url_transparent',
            'url': uplynk_preplay_url,
            'id': video_id,
            'title': video_title,
            'series': series_title,
            'episode': episode_title,
            'season_number': int_or_none(season_number),
            'episode_number': int_or_none(episode_number),
            'description': video_description,
            'release_date': release_date,
            'ie_key': 'UplynkPreplay',
        }
