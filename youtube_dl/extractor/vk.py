# encoding: utf-8
import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_str,
    unescapeHTML,
)


class VKIE(InfoExtractor):
    IE_NAME = u'vk.com'
    _VALID_URL = r'https?://vk\.com/(?:videos.*?\?.*?z=)?video(?P<id>.*?)(?:\?|%2F|$)'

    _TEST = {
        u'url': u'http://vk.com/videos-77521?z=video-77521_162222515%2Fclub77521',
        u'md5': u'0deae91935c54e00003c2a00646315f0',
        u'info_dict': {
            u'id': u'162222515',
            u'ext': u'flv',
            u'title': u'ProtivoGunz - Хуёвая песня',
            u'uploader': u'Noize MC',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_url = 'http://vk.com/al_video.php?act=show&al=1&video=%s' % video_id
        info_page = self._download_webpage(info_url, video_id)
        m_yt = re.search(r'src="(http://www.youtube.com/.*?)"', info_page)
        if m_yt is not None:
            self.to_screen(u'Youtube video detected')
            return self.url_result(m_yt.group(1), 'Youtube')
        vars_json = self._search_regex(r'var vars = ({.*?});', info_page, u'vars')
        vars = json.loads(vars_json)

        return {
            'id': compat_str(vars['vid']),
            'url': vars['url240'],
            'title': unescapeHTML(vars['md_title']),
            'thumbnail': vars['jpg'],
            'uploader': vars['md_author'],
        }
