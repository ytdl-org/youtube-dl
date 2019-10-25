# coding: utf-8
from __future__ import unicode_literals

import re
from socket import timeout

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class DTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?d\.tube/(?:#!/)?v/(?P<uploader_id>[0-9a-z.-]+)/(?P<id>[0-9a-zA-Z-_]{8,46})'
    _TESTS = [{
        'url': 'https://d.tube/v/anonyhack/QmXxj4j1prF5MUbFme4QVuGApeUw1MLq69Wf4GPBz2j2qL',
        'info_dict': {
            'id': 'QmXxj4j1prF5MUbFme4QVuGApeUw1MLq69Wf4GPBz2j2qL',
            'ext': 'mp4',
            'title': 'i wont accept it',
            'uploader_id': 'anonyhack',
        },
        'params': {
            'format': '480p',
        },
    }, {
        'url': 'https://d.tube/#!/v/hauptmann/QmSTw1aSk9Deu9YBVjpjYcaqV8AgsmTg4eN2tA8RYKTVeM',
        'info_dict': {
            'id': 'QmSTw1aSk9Deu9YBVjpjYcaqV8AgsmTg4eN2tA8RYKTVeM',
            'ext': 'mp4',
            'title': 'STATE OF THE DAPPS REPORT 25.10.2019 | D.tube talk#237',
            'description': 'md5:0180ee9bdf036b7b0ab959716cd7b6b9',
            'uploader_id': 'hauptmann',
        },
        'params': {
            'format': 'Source',
        },
    }, {
        'url': 'https://d.tube/v/whatstrending360/538648240276191',
        'info_dict': {
            'id': '538648240276191',
            'ext': 'mp4',
            'title': 'Funny Videos 2019',
            'timestamp': 1569481574,
            'upload_date': '20190926',
            'uploader': 'Funny Videos 2019',
        },
    }, {
        'url': 'https://d.tube/#!/v/jeronimorubio/XCrCtqMeywk',
        'info_dict': {
            'id': 'XCrCtqMeywk',
            'ext': 'mp4',
            'title': 'Is it Beginning to Look a lot Like Christmas in Your City?',
            'upload_date': '20191024',
            'description': 'md5:9323433bbe8b34a55d84761e5bf652af',
            'uploader': 'Jeronimo Rubio',
            'uploader_id': 'UCbbG-SIMdWSW02RYKJucddw',
        },
    }
    ]

    def _real_extract(self, url):
        DTube_api = 'https://avalon.d.tube/content/'
        uploader_id, video_id = re.match(self._VALID_URL, url).groups()

        result = self._download_json(DTube_api + uploader_id + '/' + video_id, video_id)

        metadata = result.get('json')

        if metadata.get('providerName') != "IPFS":
            video_url = metadata.get('url')
            self.to_screen('%s : video format URL %s' % (video_url, metadata.get('providerName')))
            return self.url_result(video_url)

        def canonical_url(h):
            if not h:
                return None
            return 'https://video.dtube.top/ipfs/' + h

        formats = []
        for q in ('240', '480', '720', '1080', ''):
            video_url = canonical_url(metadata.get('ipfs').get('video%shash' % q))
            if not video_url:
                continue
            format_id = (q + 'p') if q else 'Source'
            try:
                self.to_screen('%s: Checking %s video format URL' % (video_id, format_id))
                self._downloader._opener.open(video_url, timeout=5).close()
            except timeout:
                self.to_screen(
                    '%s: %s URL is invalid, skipping' % (video_id, format_id))
                continue
            formats.append({
                'format_id': format_id,
                'url': video_url,
                'height': int_or_none(q),
                'ext': 'mp4',
            })

        return {
            'id': video_id,
            'title': metadata.get('title'),
            'description': metadata.get('description'),
            'thumbnail': metadata.get('thumbnailUrl'),
            'tags': result.get('tags'),
            'duration': metadata.get('duration'),
            'formats': formats,
            'uploader_id': uploader_id,
        }
