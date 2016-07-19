# coding: utf-8
from __future__ import unicode_literals

import base64
import hashlib
import random
from .common import InfoExtractor
from ..aes import aes_cbc_decrypt
from ..utils import (
    ExtractorError,
    bytes_to_intlist,
    intlist_to_bytes,
    decode_pkcs7,
    urlencode_postdata,
    remove_start,
)


class AqstreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?aqstream\.com/[-\w]+/(?P<id>[-\w]+)'
    _TESTS = [{
        'url': 'http://aqstream.com/jtbc/JTBC',
        'only_matching': True,
    }]
    _STREAMS_CAT = 'kr'
    _STREAMS_URL = 'http://aqstream.com/list.php?cat=%s&all' % _STREAMS_CAT
    # Currently calculated in JS code as
    # `document.getElementById("theme").lastElementChild.className`
    # Not worth to messing with DOM because id of theme element might be easily
    # changed too.
    _STREAMS_SECRET = b'switch-handle'

    def _decode_streams(self, data, video_id):
        data = bytes_to_intlist(base64.b64decode(data))
        iv, ciphertext = data[:16], data[16:]
        key = bytes_to_intlist(hashlib.sha256(self._STREAMS_SECRET).digest())
        # TODO(Kagami): aes_cbc_decrypt is really slow, it takes about 1 second
        # to decode just 24kb...
        plaintext = decode_pkcs7(aes_cbc_decrypt(ciphertext, key, iv))
        text = intlist_to_bytes(plaintext).decode('utf-8')
        return self._parse_json(text, video_id)

    def _find_stream(self, streams, video_id):
        for stream_group in streams:
            group_name, group = next(iter(stream_group.items()))
            for stream in group:
                stream_name = stream[0]
                if stream_name == video_id:
                    return {
                        'name': stream_name,
                        'group_name': group_name,
                        'src': stream[1],
                        'type': stream[2],
                        'link': stream[3],
                    }

    def _get_dmp_link(self, stream, dmp_servers, video_id):
        server = 'http://' + random.choice(dmp_servers)  # Stick to JS behavior
        data = {
            'type': 'dmp',
            'id': remove_start(stream['link'], '[hls]|')
        }
        link = self._download_webpage(
            server + '/pull.php', video_id, 'Getting DMP link',
            data=urlencode_postdata(data),
            headers={
                'Referer': server,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            })
        return server + link

    def _real_extract(self, url):
        video_id = self._match_id(url).replace('-', ' ')

        streams_data = self._download_webpage(
            self._STREAMS_URL, video_id, 'Downloading streams data',
            headers={
                'X-Requested-With': 'XMLHttpRequest',
            })
        streams = self._decode_streams(streams_data, video_id)
        stream = self._find_stream(
            streams['links'][self._STREAMS_CAT], video_id)
        if not stream:
            raise ExtractorError('Cannot find stream for %s channel' % video_id,
                                 expected=True)

        if stream['src'] == 'direct' or stream['src'] == 'directstream':
            link = stream['link']
        elif stream['src'] == 'dmp':
            dmp_servers = streams['servers']['data']
            link = self._get_dmp_link(stream, dmp_servers, video_id)
        else:
            raise ExtractorError('%s links are not supported' % stream['src'])

        if stream['type'] == 'hls':
            formats = self._extract_m3u8_formats(link, video_id, 'mp4',
                                                 live=True)
            self._sort_formats(formats)
        else:
            formats = [{'url': link}]

        descriptions = streams['info'][self._STREAMS_CAT].get(
            'descriptions', {})

        return {
            'id': video_id,
            'title': video_id,
            'description': descriptions.get(stream['group_name']),
            'formats': formats,
            'is_live': True,
        }
