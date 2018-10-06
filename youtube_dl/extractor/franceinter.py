# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import month_by_name


class FranceInterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceinter\.fr/emissions/(?P<id>[^?#]+)'

    _TESTS = [
        {
            'url': 'https://www.franceinter.fr/emissions/affaires-sensibles/affaires-sensibles-07-septembre-2016',
            'md5': '9e54d7bdb6fdc02a841007f8a975c094',
            'info_dict': {
                'id': 'affaires-sensibles/affaires-sensibles-07-septembre-2016',
                'ext': 'mp3',
                'title': 'Affaire Cahuzac : le contentieux du compte en Suisse',
                'description': 'md5:401969c5d318c061f86bda1fa359292b',
                'upload_date': '20160907',
            },
        },
        {
            'note': 'Audio + video (Dailymotion embed)',
            'url': 'https://www.franceinter.fr/emissions/l-instant-m/l-instant-m-13-fevrier-2018',
            'info_dict': {
                'id': 'l-instant-m/l-instant-m-13-fevrier-2018',
                'title': 'Propagande, stéréotypes, spectaculaire : les jeux vidéo font-ils du mal à l\'Histoire ?',
                'description': 'Le youtubeur Nota Bene pour \\\"History’s Creed\\\", la nouvelle websérie d\'ARTE Creative qui explore la relation Jeux vidéo et Histoire',
                'upload_date': '20180213',
            },
            'playlist_count': 2,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        audio_url = self._search_regex(
            r'(?s)<div[^>]+class=["\']page-diffusion["\'][^>]*>.*?<button[^>]+data-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'audio url', group='url')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        upload_date_str = self._search_regex(
            r'class=["\']\s*cover-emission-period\s*["\'][^>]*>[^<]+\s+(\d{1,2}\s+[^\s]+\s+\d{4})<',
            webpage, 'upload date', fatal=False)
        if upload_date_str:
            upload_date_list = upload_date_str.split()
            upload_date_list.reverse()
            upload_date_list[1] = '%02d' % (month_by_name(upload_date_list[1], lang='fr') or 0)
            upload_date_list[2] = '%02d' % int(upload_date_list[2])
            upload_date = ''.join(upload_date_list)
        else:
            upload_date = None

        audio = {
            'id': video_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'formats': [{
                'url': audio_url,
                'vcodec': 'none',
            }],
        }

        # If there is a video, return playlist of audio + video, else just audio
        maybe_video_uuid = re.search(r'data-video-anchor-target=["\']([^"\']+)', webpage)
        if maybe_video_uuid:
            video_uuid = maybe_video_uuid.group(1)
            video_url = self._search_regex(
                r'(?sx)data-uuid=["\']%s.*?<iframe[^>]*src=["\']([^"\']+)' % video_uuid,
                webpage, 'video url', fatal=False, group=1)

            if video_url:
                video = {'_type': 'url', 'url': video_url}

                return {
                    '_type': 'playlist',
                    'id': video_id,
                    'title': title,
                    'description': description,
                    'upload_date': upload_date,
                    'entries': [audio, video]
                }
            else:
                return audio
        else:
            return audio
