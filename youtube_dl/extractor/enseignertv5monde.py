# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate


class EnseignerTV5MondeIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?enseigner\.tv5monde\.com\/videos-sans-fiche\/(?P<id>[a-zA-Z0-9\-]+)'
    _TESTS = [
        {
            'url': 'https://enseigner.tv5monde.com/videos-sans-fiche/la-culture-en-france',
            'md5': 'bb9e4c4701c1873a3790a0a33eb89ce6',
            'info_dict': {
                'id': 'la-culture-en-france',
                'ext': 'mp4',
                'title': 'La culture en France',
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        },
        {
            'url': 'https://enseigner.tv5monde.com/videos-sans-fiche/les-chapeaux-de-la-maison-michel',
            'md5': 'bdfc21506aee0ffa2afd823f1c44ce66',
            'info_dict': {
                'id': 'les-chapeaux-de-la-maison-michel',
                'ext': 'mp4',
                'title': 'Les chapeaux de la Maison Michel',
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        d = self._extract_jwplayer_data(webpage, video_id, require_title=False)

        d.update({
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'release_date': unified_strdate(self._html_search_regex(r'itemprop="datePublished"[^>]*>([0-9/]+)</time>', webpage, 'release date', fatal=False))})

        return d
