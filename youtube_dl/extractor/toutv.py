# coding: utf-8
import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate,
)


class TouTvIE(InfoExtractor):
    IE_NAME = u'tou.tv'
    _VALID_URL = r'https?://www\.tou\.tv/(?P<id>[a-zA-Z0-9_-]+(?:/(?P<episode>S[0-9]+E[0-9]+)))'

    _TEST = {
        u'url': u'http://www.tou.tv/30-vies/S04E41',
        u'file': u'30-vies_S04E41.mp4',
        u'info_dict': {
            u'title': u'30 vies Saison 4 / Épisode 41',
            u'description': u'md5:da363002db82ccbe4dafeb9cab039b09',
            u'age_limit': 8,
            u'uploader': u'Groupe des Nouveaux Médias',
            u'duration': 1296,
            u'upload_date': u'20131118',
            u'thumbnail': u'http://static.tou.tv/medias/images/2013-11-18_19_00_00_30VIES_0341_01_L.jpeg',
        },
        u'params': {
            u'skip_download': True,  # Requires rtmpdump
        },
        u'xskip': 'Only available in Canada'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        mediaId = self._search_regex(
            r'"idMedia":\s*"([^"]+)"', webpage, u'media ID')

        # TODO test from de
        streams_url = u'http://release.theplatform.com/content.select?pid=' + mediaId
        streams_webpage = self._download_webpage(
            streams_url, video_id, note=u'Downloading stream list')

        streams_doc = xml.etree.ElementTree.fromstring(
            streams_webpage.encode('utf-8'))
        video_url = next(n.text
                         for n in streams_doc.findall('.//choice/url')
                         if u'//ad.doubleclick' not in n.text)
        if video_url.endswith('/Unavailable.flv'):
            raise ExtractorError(
                u'Access to this video is blocked from outside of Canada',
                expected=True)

        duration_str = self._html_search_meta(
            'video:duration', webpage, u'duration')
        duration = int(duration_str) if duration_str else None
        upload_date_str = self._html_search_meta(
            'video:release_date', webpage, u'upload date')
        upload_date = unified_strdate(upload_date_str) if upload_date_str else None

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': video_url,
            'description': self._og_search_description(webpage),
            'uploader': self._dc_search_uploader(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'age_limit': self._media_rating_search(webpage),
            'duration': duration,
            'upload_date': upload_date,
            'ext': 'mp4',
        }
