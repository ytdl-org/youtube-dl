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
            'description':
                u'Tommia harmittaa kun sukulaiset ovat tulossa pilaamaan '
                'mukavan perhejoulun. Muuttuuko mieli isosta yllätyksestä? '
                'Joulun erikoisjakson on ohjannut Jalmari Helander.',
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
        # This extractor will fetch some basic info and then lead to Kaltura
        # extractor.
        props = {
            '_type': 'url_transparent',
            'ie_key': 'Kaltura'
        }

        # Get essential data
        props['id'] = self._match_id(url)
        webpage = self._download_webpage(url, props['id'])

        # Try to extract title from OpenGraph metadata
        _title = self._og_search_title(webpage, fatal=False)

        # Fallback #1: try to extract title from page body
        if _title is None:
            _title = self._html_search_regex(
                r'<h1>([^<]+)',
                webpage,
                'title',
                fatal=False
            )

        # Fallback #2: let Kaltura extractor give the title (it should have it)
        # If title is found from Areena page, use it
        if _title is not None:
            props['title'] = _title

        # Same thing for description
        _description = self._og_search_description(webpage)

        # No Areena fallback here, the page layout is so ambiguous we cannot
        # guarantee that the right description would match in series pages
        if _description is not None:
            props['description'] = _description

        # player_url is used for getting partner_id and entry_id for Kaltura
        # extractor
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

        props['url'] = 'kaltura:%s:%s' % (partner_id, entry_id)

        return props
