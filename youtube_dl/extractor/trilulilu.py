import json
import re

from .common import InfoExtractor


class TriluliluIE(InfoExtractor):
    _VALID_URL = r'(?x)(?:https?://)?(?:www\.)?trilulilu\.ro/video-(?P<category>[^/]+)/(?P<video_id>[^/]+)'
    _TEST = {
        u"url": u"http://www.trilulilu.ro/video-animatie/big-buck-bunny-1",
        u'file': u"big-buck-bunny-1.mp4",
        u'info_dict': {
            u"title": u"Big Buck Bunny",
            u"description": u":) pentru copilul din noi",
        },
        # Server ignores Range headers (--test)
        u"params": {
            u"skip_download": True
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)

        log_str = self._search_regex(
            r'block_flash_vars[ ]=[ ]({[^}]+})', webpage, u'log info')
        log = json.loads(log_str)

        format_url = (u'http://fs%(server)s.trilulilu.ro/%(hash)s/'
                      u'video-formats2' % log)
        format_doc = self._download_xml(
            format_url, video_id,
            note=u'Downloading formats',
            errnote=u'Error while downloading formats')
 
        video_url_template = (
            u'http://fs%(server)s.trilulilu.ro/stream.php?type=video'
            u'&source=site&hash=%(hash)s&username=%(userid)s&'
            u'key=ministhebest&format=%%s&sig=&exp=' %
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

