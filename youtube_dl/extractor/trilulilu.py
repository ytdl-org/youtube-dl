from __future__ import unicode_literals

import json

from .common import InfoExtractor


class TriluliluIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?trilulilu\.ro/video-[^/]+/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.trilulilu.ro/video-animatie/big-buck-bunny-1',
        'info_dict': {
            'id': 'big-buck-bunny-1',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'description': ':) pentru copilul din noi',
        },
        # Server ignores Range headers (--test)
        'params': {
            'skip_download': True
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)

        log_str = self._search_regex(
            r'block_flash_vars[ ]=[ ]({[^}]+})', webpage, 'log info')
        log = json.loads(log_str)

        format_url = ('http://fs%(server)s.trilulilu.ro/%(hash)s/'
                      'video-formats2' % log)
        format_doc = self._download_xml(
            format_url, video_id,
            note='Downloading formats',
            errnote='Error while downloading formats')

        video_url_template = (
            'http://fs%(server)s.trilulilu.ro/stream.php?type=video'
            '&source=site&hash=%(hash)s&username=%(userid)s&'
            'key=ministhebest&format=%%s&sig=&exp=' %
            log)
        formats = [
            {
                'format': fnode.text,
                'url': video_url_template % fnode.text,
                'ext': fnode.text.partition('-')[0]
            }

            for fnode in format_doc.findall('./formats/format')
        ]

        return {
            '_type': 'video',
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
