# coding: utf-8
import re

from .common import InfoExtractor


class RadioFranceIE(InfoExtractor):
    _VALID_URL = r'^https?://maison\.radiofrance\.fr/radiovisions/(?P<id>[^?#]+)'
    IE_NAME = u'radiofrance'

    _TEST = {
        u'url': u'http://maison.radiofrance.fr/radiovisions/one-one',
        u'file': u'one-one.ogg',
        u'md5': u'bdbb28ace95ed0e04faab32ba3160daf',
        u'info_dict': {
            u"title": u"One to one",
            u"description": u"Plutôt que d'imaginer la radio de demain comme technologie ou comme création de contenu, je veux montrer que quelles que soient ses évolutions, j'ai l'intime conviction que la radio continuera d'être un grand média de proximité pour les auditeurs.",
            u"uploader": u"Thomas Hercouët",
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>(.*?)</h1>', webpage, u'title')
        description = self._html_search_regex(
            r'<div class="bloc_page_wrapper"><div class="text">(.*?)</div>',
            webpage, u'description', fatal=False)
        uploader = self._html_search_regex(
            r'<div class="credit">&nbsp;&nbsp;&copy;&nbsp;(.*?)</div>',
            webpage, u'uploader', fatal=False)

        formats_str = self._html_search_regex(
            r'class="jp-jplayer[^"]*" data-source="([^"]+)">',
            webpage, u'audio URLs')
        formats = [
            {
                'format_id': fm[0],
                'url': fm[1],
                'vcodec': 'none',
            }
            for fm in
            re.findall(r"([a-z0-9]+)\s*:\s*'([^']+)'", formats_str)
        ]
        # No sorting, we don't know any more about these formats

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'uploader': uploader,
        }
