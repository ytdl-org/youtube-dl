import re

from .mtv import MTVIE, _media_xml_tag


class SouthParkStudiosIE(MTVIE):
    IE_NAME = u'southparkstudios.com'
    _VALID_URL = r'https?://www\.southparkstudios\.com/(clips|full-episodes)/(?P<id>.+?)(\?|#|$)'

    _FEED_URL = 'http://www.southparkstudios.com/feeds/video-player/mrss'

    _TEST = {
        u'url': u'http://www.southparkstudios.com/clips/104437/bat-daded#tab=featured',
        u'file': u'a7bff6c2-ed00-11e0-aca6-0026b9414f30.mp4',
        u'info_dict': {
            u'title': u'Bat Daded',
            u'description': u'Randy disqualifies South Park by getting into a fight with Bat Dad.',
        },
    }

    # Overwrite MTVIE properties we don't want
    _TESTS = []

    def _get_thumbnail_url(self, uri, itemdoc):
        search_path = '%s/%s' % (_media_xml_tag('group'), _media_xml_tag('thumbnail'))
        thumb_node = itemdoc.find(search_path)
        if thumb_node is None:
            return None
        else:
            return thumb_node.attrib['url']

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        mgid = self._search_regex(r'swfobject.embedSWF\(".*?(mgid:.*?)"',
                                  webpage, u'mgid')
        return self._get_videos_info(mgid)
