from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unescapeHTML,
    find_xpath_attr,
    smuggle_url,
    determine_ext,
    ExtractorError,
)
from .senateisvp import SenateISVPIE


class CSpanIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?c-span\.org/video/\?(?P<id>[0-9a-f]+)'
    IE_DESC = 'C-SPAN'
    _TESTS = [{
        'url': 'http://www.c-span.org/video/?313572-1/HolderonV',
        'md5': '94b29a4f131ff03d23471dd6f60b6a1d',
        'info_dict': {
            'id': '315139',
            'ext': 'mp4',
            'title': 'Attorney General Eric Holder on Voting Rights Act Decision',
            'description': 'Attorney General Eric Holder speaks to reporters following the Supreme Court decision in [Shelby County v. Holder], in which the court ruled that the preclearance provisions of the Voting Rights Act could not be enforced.',
        },
        'skip': 'Regularly fails on travis, for unknown reasons',
    }, {
        'url': 'http://www.c-span.org/video/?c4486943/cspan-international-health-care-models',
        'md5': '8e5fbfabe6ad0f89f3012a7943c1287b',
        'info_dict': {
            'id': 'c4486943',
            'ext': 'mp4',
            'title': 'CSPAN - International Health Care Models',
            'description': 'md5:7a985a2d595dba00af3d9c9f0783c967',
        }
    }, {
        'url': 'http://www.c-span.org/video/?318608-1/gm-ignition-switch-recall',
        'md5': '2ae5051559169baadba13fc35345ae74',
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
        video_type = None
        webpage = self._download_webpage(url, video_id)
        # We first look for clipid, because clipprog always appears before
        patterns = [r'id=\'clip(%s)\'\s*value=\'([0-9]+)\'' % t for t in ('id', 'prog')]
        results = list(filter(None, (re.search(p, webpage) for p in patterns)))
        if results:
            matches = results[0]
            video_type, video_id = matches.groups()
            video_type = 'clip' if video_type == 'id' else 'program'
        else:
            m = re.search(r'data-(?P<type>clip|prog)id=["\'](?P<id>\d+)', webpage)
            if m:
                video_id = m.group('id')
                video_type = 'program' if m.group('type') == 'prog' else 'clip'
            else:
                senate_isvp_url = SenateISVPIE._search_iframe_url(webpage)
                if senate_isvp_url:
                    title = self._og_search_title(webpage)
                    surl = smuggle_url(senate_isvp_url, {'force_title': title})
                    return self.url_result(surl, 'SenateISVP', video_id, title)
        if video_type is None or video_id is None:
            raise ExtractorError('unable to find video id and type')

        def get_text_attr(d, attr):
            return d.get(attr, {}).get('#text')

        data = self._download_json(
            'http://www.c-span.org/assets/player/ajax-player.php?os=android&html5=%s&id=%s' % (video_type, video_id),
            video_id)['video']
        if data['@status'] != 'Success':
            raise ExtractorError('%s said: %s' % (self.IE_NAME, get_text_attr(data, 'error')), expected=True)

        doc = self._download_xml(
            'http://www.c-span.org/common/services/flashXml.php?%sid=%s' % (video_type, video_id),
            video_id)

        description = self._html_search_meta('description', webpage)

        title = find_xpath_attr(doc, './/string', 'name', 'title').text
        thumbnail = find_xpath_attr(doc, './/string', 'name', 'poster').text

        files = data['files']
        capfile = get_text_attr(data, 'capfile')

        entries = []
        for partnum, f in enumerate(files):
            formats = []
            for quality in f['qualities']:
                formats.append({
                    'format_id': '%s-%sp' % (get_text_attr(quality, 'bitrate'), get_text_attr(quality, 'height')),
                    'url': unescapeHTML(get_text_attr(quality, 'file')),
                    'height': int_or_none(get_text_attr(quality, 'height')),
                    'tbr': int_or_none(get_text_attr(quality, 'bitrate')),
                })
            if not formats:
                path = unescapeHTML(get_text_attr(f, 'path'))
                if not path:
                    continue
                formats = self._extract_m3u8_formats(
                    path, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls') if determine_ext(path) == 'm3u8' else [{'url': path, }]
            self._sort_formats(formats)
            entries.append({
                'id': '%s_%d' % (video_id, partnum + 1),
                'title': (
                    title if len(files) == 1 else
                    '%s part %d' % (title, partnum + 1)),
                'formats': formats,
                'description': description,
                'thumbnail': thumbnail,
                'duration': int_or_none(get_text_attr(f, 'length')),
                'subtitles': {
                    'en': [{
                        'url': capfile,
                        'ext': determine_ext(capfile, 'dfxp')
                    }],
                } if capfile else None,
            })

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
