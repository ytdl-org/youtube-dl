# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NationalArchivesUkIE(InfoExtractor):
    _VALID_URL = r'https?://media.nationalarchives.gov.uk/index.php/(?P<id>.*)/?'
    _TEST = {
        'url': 'http://media.nationalarchives.gov.uk/index.php/webinar-using-discovery-national-archives-online-catalogue/',
        'info_dict': {
            'id': 'Mrj4DVp2zeA',
            'ext': 'mp4',

            'upload_date': '20150204',
            'uploader_id': 'NationalArchives08',
            'title': 'Webinar: Using Discovery, The National Archives’ online catalogue',
            'uploader': 'The National Archives UK',
            'description': 'md5:a236581cd2449dd2df4f93412f3f01c6'
        }

    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        youtube_url = re.search(r'https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)(\w*)(&(amp;)?[\w\?=]*)?',
                                webpage, re.MULTILINE).group(0)
        self.to_screen('Youtube video detected')

        return self.url_result(youtube_url, ie='Youtube')
