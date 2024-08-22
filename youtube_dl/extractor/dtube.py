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
        # old test: fail
        'url': 'https://d.tube/#!/v/broncnutz/x380jtr1',
        'md5': '9f29088fa08d699a7565ee983f56a06e',
        'info_dict': {
            'id': 'x380jtr1',
            'ext': 'mp4',
            'title': 'Lefty 3-Rings is Back Baby!! NCAA Picks',
            'description': 'md5:60be222088183be3a42f196f34235776',
            'uploader_id': 'broncnutz',
            'upload_date': '20190107',
            'timestamp': 1546854054,
        },
        'params': {
            'format': '480p',
        },
    }, {
        # ipfs
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
        # facebook
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
        # youtube
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
    }]

    def _real_extract(self, url):
        uploader_id, video_id = re.match(self._VALID_URL, url).groups()

        result = self._download_json(
            'https://avalon.d.tube/content/%s/%s' % (uploader_id, video_id),
            video_id)

        metadata = result.get('json')
        title = metadata.get('title') or result['title']

        if metadata.get('providerName') != 'IPFS':
            video_url = metadata.get('url')
            return self.url_result(video_url)

        def canonical_url(h):
            if not h:
                return None
            return 'https://video.dtube.top/ipfs/' + h

        formats = []
        for q in ('240', '480', '720', '1080', ''):
            video_url = canonical_url(
                metadata.get('ipfs').get('video%shash' % q))
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
            'title': title,
            'description': metadata.get('description'),
            'thumbnail': metadata.get('thumbnailUrl'),
            'tags': result.get('tags'),
            'duration': metadata.get('duration'),
            'formats': formats,
            'uploader_id': uploader_id,
        }
