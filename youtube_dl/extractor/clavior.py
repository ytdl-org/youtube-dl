from __future__ import unicode_literals

import re
import ast

from .common import InfoExtractor


class ClaviorIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?(clavior|bofiaz)\.com/(?P<key>.*)/index.php\?option=com_content&view=article&id=(?P<id>.*):ghhghgh&catid=(?P<catid>[0-9]+):(?P<genre>[a-z]+)-&Itemid=(?P<itemid>[0-9]+)'
    _TEST = {
        'url': 'http://clavior.com/kk54bvb7gyt8/index.php?option=com_content&view=article&id=685549200:ghhghgh&catid=7:drame-&Itemid=17',
        'info_dict': {
            'id': '685549200',
            'ext': 'mp4',
            'title': 'Tolkien (2019) ',
            'description': 'Revient sur la jeunesse et les années d’apprentissage du célèbre auteur J.R.R. Tolkien. Orphelin, il trouve l’amitié, l’amour et l’inspiration au sein d’un groupe de camarades de son école. Mais la Première Guerre Mondiale éclate et menace de détruire cette « communauté ». Ce sont toutes ces expériences qui vont inspirer Tolkien dans l’écriture de ses romans de la Terre du Milieu "Bilbo le Hobbit" et "Le Seigneur des Anneaux".',
            'thumbnail': r're:^https?://image\.tmdb\.org/t/p/original/.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        if 'test' not in self._downloader.params:
            self._downloader.report_warning('For now, this extractor only supports the 30 second previews. Patches welcome!')

        mobj = re.match(self._VALID_URL, url)
        id = mobj.group('id')

        webpage = self._download_webpage(url, id)
        nexturl = self._search_regex(r'<iframe src="(.*?)"', webpage, "Iframe src")

        title = self._search_regex(r'<title>(.*?)</title>', webpage, "title")
        description = self._search_regex(r'<p style="text-align: left;">\s*(([\s\S])*?)\s*</p>', webpage, "description")

        thumbnail = self._search_regex(r'<img src="(.*?)"', webpage, "thumbnail")

        webpage = self._download_webpage(nexturl, id)
        nexturl = self._search_regex(r"""<a onclick="window.location.href='(.*?)'""", webpage, "Onclick location")

        webpage = self._download_webpage(nexturl, id)
        data_json = self._search_regex(r'sources: \[\s*(([\s\S])*?)\s*\],', webpage, "data JSON")

        data_json = data_json.replace("'", '"').replace('file', '"file"').replace('label', '"label"').replace('type', '"type"').replace('},', '}').replace('\t', '')

        formats = []
        for line in data_json.splitlines():
            data = ast.literal_eval(line)
            formats.append({
                'format_id': 'full',
                'url': data.get('file'),
                'preference': -1 if data.get('label') == '720p' else -2,
                'ext': data.get('type'),
            })

        return {
            'id': id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
