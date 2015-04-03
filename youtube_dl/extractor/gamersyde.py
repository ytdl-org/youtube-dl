# coding: utf-8
from __future__ import unicode_literals
import re
import json
import time
from .common import InfoExtractor


class GamersydeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gamersyde\.com/hqstream_'
    _TEST = {
        'url': 'http://www.gamersyde.com/hqstream_bloodborne_birth_of_a_hero-34371_en.html',
        'md5': 'f38d400d32f19724570040d5ce3a505f',
        'info_dict': {
            'id': '34371',
            'ext': 'mp4',
            'title': 'Bloodborne - Birth of a hero',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _calculateDuration(self, durationString):
        duration = time.strptime(durationString, "%M minutes %S seconds")
        return duration.tm_min * 60 + duration.tm_sec

    def _fixJsonSyntax(self, json):

        json = re.sub(r"{\s*(\w)", r'{"\1', json)
        json = re.sub(r",\s*(\w)", r',"\1', json)
        json = re.sub(r"(\w): ", r'\1":', json)
        json = re.sub(r",\s*}", "}", json, flags=re.DOTALL)
        json = re.sub(r",\s*]", "]", json, flags=re.DOTALL)

        return json

    def _real_extract(self, url):

        video_id = self._search_regex(r'-(.*?)_[a-z]{2}.html$', url, 'video_id')
        webpage = self._download_webpage(url, video_id)

        filesJson = self._search_regex(r'playlist: (.*?)\}\);', webpage, 'files', flags=re.DOTALL)
        filesJson = self._fixJsonSyntax(filesJson)

        data = json.loads(filesJson)
        playlist = data[0]

        formats = []

        title = re.sub(r"[0-9]+ - ", "", playlist['title'])

        for playlistEntry in playlist['sources']:
            format = {
                'url': playlistEntry['file'],
                'format_id': playlistEntry['label']
            }

            formats.append(format)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': playlist['image']
            }
