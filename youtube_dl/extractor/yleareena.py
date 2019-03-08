# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    RegexNotFoundError,
    url_or_none
)


class YleAreenaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:areena|arenan).yle.fi/(?P<id>[0-9]-[0-9]+)'
    _GEO_COUNTRIES = ['FI']

    _TEST = {
        'url': 'https://areena.yle.fi/1-4256816',
        'md5': 'b9658c5960a8c2ca4ba8f1b0ff079df2',
        'info_dict': {
            'id': '1_iq074q8b',
            'ext': 'mxf',
            'title': 'Luottomies | Luottomies jouluspeciaali',
            'description': u'Tommia harmittaa kun sukulaiset ovat tulossa pilaamaan mukavan perhejoulun. Muuttuuko mieli isosta yllätyksestä? Joulun erikoisjakson on ohjannut Jalmari Helander.',
            'upload_date': '20171207',
            'height': 1080,
            'width': 1920,
            'fps': 25,
            'duration': 1302,
            'timestamp': 1512633989,
            'extractor': 'Kaltura',
            'uploader_id': 'ovp@yle.fi',
            'webpage_url_basename': '1-4256816',
            'webpage_url': 'https://areena.yle.fi/1-4256816'
        }
    }

    def _real_extract(self, url):
        # Get essential data
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Extract essential metadata from Areena webpage
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        # player_url is not used for the actual extraction,
        # just for getting partner_id and entry_id for Kaltura extractor
        # (though it is still required or else the extraction will fail)
        try:
            player_url = url_or_none(
                self._og_search_property('video:secure_url', webpage)
            )
        except RegexNotFoundError:
            player_url = None

        # If this backup fails extractor will error out
        player_url = url_or_none(
            self._og_search_property('video:url', webpage)
        )

        if player_url is None:
            raise RegexNotFoundError('Cannot find player url')

        # Get Kaltura identifiers from player_url
        partner_id = self._search_regex(
            r'/p/([0-9]+)',
            player_url,
            'Kaltura partner id'
        )

        entry_id = self._search_regex(
            r'/entry_id/([0-9]_[0-9a-z]+)',
            player_url,
            'Kaltura entry id'
        )

        kaltura_url = 'kaltura:%s:%s' % (partner_id, entry_id)

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': kaltura_url,
            'ie_key': 'Kaltura',
            'title': title,
            'description': description
        }
