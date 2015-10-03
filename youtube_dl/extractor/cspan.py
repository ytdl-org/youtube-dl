from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unescapeHTML,
    find_xpath_attr,
    smuggle_url,
    determine_ext,
)
from .senateisvp import SenateISVPIE


class CSpanIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?c-span\.org/video/\?(?P<id>[0-9a-f]+)'
    IE_DESC = 'C-SPAN'
    _TESTS = [{
        'url': 'http://www.c-span.org/video/?313572-1/HolderonV',
        'md5': '067803f994e049b455a58b16e5aab442',
        'info_dict': {
            'id': '315139',
            'ext': 'mp4',
            'title': 'Attorney General Eric Holder on Voting Rights Act Decision',
            'description': 'Attorney General Eric Holder speaks to reporters following the Supreme Court decision in [Shelby County v. Holder], in which the court ruled that the preclearance provisions of the Voting Rights Act could not be enforced.',
        },
        'skip': 'Regularly fails on travis, for unknown reasons',
    }, {
        'url': 'http://www.c-span.org/video/?c4486943/cspan-international-health-care-models',
        'md5': '4eafd1e91a75d2b1e6a3cbd0995816a2',
        'info_dict': {
            'id': 'c4486943',
            'ext': 'mp4',
            'title': 'CSPAN - International Health Care Models',
            'description': 'md5:7a985a2d595dba00af3d9c9f0783c967',
        }
    }, {
        'url': 'http://www.c-span.org/video/?318608-1/gm-ignition-switch-recall',
        'md5': '446562a736c6bf97118e389433ed88d4',
        'info_dict': {
            'id': '342759',
            'ext': 'mp4',
            'title': 'General Motors Ignition Switch Recall',
            'duration': 14848,
            'description': 'md5:118081aedd24bf1d3b68b3803344e7f3'
        },
    }, {
        # Video from senate.gov
        'url': 'http://www.c-span.org/video/?104517-1/immigration-reforms-needed-protect-skilled-american-workers',
        'info_dict': {
            'id': 'judiciary031715',
            'ext': 'flv',
            'title': 'Immigration Reforms Needed to Protect Skilled American Workers',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        matches = re.search(r'data-(prog|clip)id=\'([0-9]+)\'', webpage)
        if matches:
            video_type, video_id = matches.groups()
            if video_type == 'prog':
                video_type = 'program'
        else:
            senate_isvp_url = SenateISVPIE._search_iframe_url(webpage)
            if senate_isvp_url:
                title = self._og_search_title(webpage)
                surl = smuggle_url(senate_isvp_url, {'force_title': title})
                return self.url_result(surl, 'SenateISVP', video_id, title)

        data = self._download_json(
            'http://c-spanvideo.org/videoLibrary/assets/player/ajax-player.php?os=android&html5=%s&id=%s' % (video_type, video_id),
            video_id)

        doc = self._download_xml(
            'http://www.c-span.org/common/services/flashXml.php?%sid=%s' % (video_type, video_id),
            video_id)

        description = self._html_search_meta('description', webpage)

        title = find_xpath_attr(doc, './/string', 'name', 'title').text
        thumbnail = find_xpath_attr(doc, './/string', 'name', 'poster').text

        files = data['video']['files']
        try:
            capfile = data['video']['capfile']['#text']
        except KeyError:
            capfile = None

        entries = [{
            'id': '%s_%d' % (video_id, partnum + 1),
            'title': (
                title if len(files) == 1 else
                '%s part %d' % (title, partnum + 1)),
            'url': unescapeHTML(f['path']['#text']),
            'description': description,
            'thumbnail': thumbnail,
            'duration': int_or_none(f.get('length', {}).get('#text')),
            'subtitles': {
                'en': [{
                    'url': capfile,
                    'ext': determine_ext(capfile, 'dfxp')
                }],
            } if capfile else None,
        } for partnum, f in enumerate(files)]

        if len(entries) == 1:
            entry = dict(entries[0])
            entry['id'] = 'c' + video_id if video_type == 'clip' else video_id
            return entry
        else:
            return {
                '_type': 'playlist',
                'entries': entries,
                'title': title,
                'id': 'c' + video_id if video_type == 'clip' else video_id,
            }
