# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    ExtractorError,
    float_or_none,
    int_or_none,
    str_to_int,
)


class PlayFMIE(InfoExtractor):
    IE_NAME = 'play.fm'
    _VALID_URL = r'https?://(?:www\.)?play\.fm/[^?#]*(?P<upload_date>[0-9]{8})(?P<id>[0-9]{6})(?:$|[?#])'

    _TEST = {
        'url': 'http://www.play.fm/recording/leipzigelectronicmusicbatofarparis_fr20140712137220',
        'md5': 'c505f8307825a245d0c7ad1850001f22',
        'info_dict': {
            'id': '137220',
            'ext': 'mp3',
            'title': 'LEIPZIG ELECTRONIC MUSIC @ Batofar (Paris,FR) - 2014-07-12',
            'uploader': 'Sven Tasnadi',
            'uploader_id': 'sventasnadi',
            'duration': 5627.428,
            'upload_date': '20140712',
            'view_count': int,
            'comment_count': int,
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        upload_date = mobj.group('upload_date')

        rec_data = compat_urllib_parse.urlencode({'rec_id': video_id})
        req = compat_urllib_request.Request(
            'http://www.play.fm/flexRead/recording', data=rec_data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        rec_doc = self._download_xml(req, video_id)

        error_node = rec_doc.find('./error')
        if error_node is not None:
            raise ExtractorError('An error occured: %s (code %s)' % (
                error_node.text, rec_doc.find('./status').text))

        recording = rec_doc.find('./recording')
        title = recording.find('./title').text
        view_count = str_to_int(recording.find('./stats/playcount').text)
        comment_count = str_to_int(recording.find('./stats/comments').text)
        duration = float_or_none(recording.find('./duration').text, scale=1000)
        thumbnail = recording.find('./image').text

        artist = recording.find('./artists/artist')
        uploader = artist.find('./name').text
        uploader_id = artist.find('./slug').text

        video_url = '%s//%s/%s/%s/offset/0/sh/%s/rec/%s/jingle/%s/loc/%s' % (
            'http:', recording.find('./url').text,
            recording.find('./_class').text, recording.find('./file_id').text,
            rec_doc.find('./uuid').text, video_id,
            rec_doc.find('./jingle/file_id').text,
            'http%3A%2F%2Fwww.play.fm%2Fplayer',
        )

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp3',
            'filesize': int_or_none(recording.find('./size').text),
            'title': title,
            'upload_date': upload_date,
            'view_count': view_count,
            'comment_count': comment_count,
            'duration': duration,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
        }
