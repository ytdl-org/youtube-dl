# coding: utf-8
from __future__ import unicode_literals
import re
import time

from .common import InfoExtractor


class GamersydeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gamersyde\.com/hqstream_'
    _TESTS = [{
        'url': 'http://www.gamersyde.com/hqstream_bloodborne_birth_of_a_hero-34371_en.html',
        'md5': 'f38d400d32f19724570040d5ce3a505f',
        'info_dict': {
            'id': '34371',
            'ext': 'mp4',
            'duration': 372,
            'title': 'Bloodborne - Birth of a hero',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.gamersyde.com/hqstream_dark_souls_ii_scholar_of_the_first_sin_gameplay_part_1-34417_en.html',
        'md5': '94bd7c3feff3275576cf5cb6c8a3a720',
        'info_dict': {
            'id': '34417',
            'ext': 'mp4',
            'duration': 270,
            'title': 'Dark Souls II: Scholar of the First Sin - Gameplay - Part 1',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.gamersyde.com/hqstream_grand_theft_auto_v_heists_trailer-33786_en.html',
        'md5': '65e442f5f340d571ece8c80d50700369',
        'info_dict': {
            'id': '33786',
            'ext': 'mp4',
            'duration': 59,
            'title': 'Grand Theft Auto V - Heists Trailer',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }
    ]

    def _calculateDuration(self, durationString):
        if (durationString.find("minutes") > -1):
            duration = time.strptime(durationString, "%M minutes %S seconds")
        else:
            duration = time.strptime(durationString, "%S seconds")
        return duration.tm_min * 60 + duration.tm_sec

    def _fixJsonSyntax(self, json):

        json = re.sub(r",\s*}", "}", json, flags=re.DOTALL)
        json = re.sub(r",\s*]", "]", json, flags=re.DOTALL)
        json = json.replace('file: "', '"file": "')
        json = json.replace('title: "', '"title": "')
        json = json.replace('label: "', '"label": "')
        json = json.replace('image: "', '"image": "')
        json = json.replace('sources: [', '"sources": [')
        return json

    def _real_extract(self, url):

        video_id = self._search_regex(r'-(.*?)_[a-z]{2}.html$', url, 'video_id')
        webpage = self._download_webpage(url, video_id)

        filesJson = self._search_regex(r'playlist: (.*?)\}\);', webpage, 'files', flags=re.DOTALL)
        data = self._parse_json(filesJson,video_id, transform_source=self._fixJsonSyntax)
        
        playlist = data[0]

        formats = []

        title = re.sub(r"[0-9]+ - ", "", playlist['title'])
        
        length = self._search_regex(r'(([0-9]{1,2} minutes ){0,1}[0-9]{1,2} seconds)', webpage, 'length')
        duration = self._calculateDuration(length)

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
            'duration': duration,
            'thumbnail': playlist['image']
            }
