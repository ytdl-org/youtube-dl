# coding: utf-8
from __future__ import unicode_literals

import json
import re
from socket import timeout

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class DTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?d\.tube/(?:#!/)?v/(?P<uploader_id>[0-9a-z.-]+)/(?P<id>[0-9a-z]{8})'
    _TEST = {
        'url': 'https://d.tube/#!/v/benswann/zqd630em',
        'md5': 'a03eaa186618ffa7a3145945543a251e',
        'info_dict': {
            'id': 'zqd630em',
            'ext': 'mp4',
            'title': 'Reality Check: FDA\'s Disinformation Campaign on Kratom',
            'description': 'md5:700d164e066b87f9eac057949e4227c2',
            'uploader_id': 'benswann',
            'upload_date': '20180222',
            'timestamp': 1519328958,
        },
        'params': {
            'format': '480p',
        },
    }

    def _real_extract(self, url):
        uploader_id, video_id = re.match(self._VALID_URL, url).groups()
        result = self._download_json('https://api.steemit.com/', video_id, data=json.dumps({
            'jsonrpc': '2.0',
            'method': 'get_content',
            'params': [uploader_id, video_id],
        }).encode())['result']

        metadata = json.loads(result['json_metadata'])
        video = metadata['video']
        content = video['content']
        info = video.get('info', {})
        title = info.get('title') or result['title']

        def canonical_url(h):
            if not h:
                return None
            return 'https://ipfs.io/ipfs/' + h

        formats = []
        for q in ('240', '480', '720', '1080', ''):
            video_url = canonical_url(content.get('video%shash' % q))
            if not video_url:
                continue
            format_id = (q + 'p') if q else 'Source'
            try:
                self.to_screen('%s: Checking %s video format URL' % (video_id, format_id))
                self._downloader._opener.open(video_url, timeout=5).close()
            except timeout as e:
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
            'description': content.get('description'),
            'thumbnail': canonical_url(info.get('snaphash')),
            'tags': content.get('tags') or metadata.get('tags'),
            'duration': info.get('duration'),
            'formats': formats,
            'timestamp': parse_iso8601(result.get('created')),
            'uploader_id': uploader_id,
        }
