# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    unsmuggle_url,
    url_or_none,
)
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)


class SenateISVPIE(InfoExtractor):
    _COMM_MAP = [
        ['ag', '76440', 'http://ag-f.akamaihd.net'],
        ['aging', '76442', 'http://aging-f.akamaihd.net'],
        ['approps', '76441', 'http://approps-f.akamaihd.net'],
        ['armed', '76445', 'http://armed-f.akamaihd.net'],
        ['banking', '76446', 'http://banking-f.akamaihd.net'],
        ['budget', '76447', 'http://budget-f.akamaihd.net'],
        ['cecc', '76486', 'http://srs-f.akamaihd.net'],
        ['commerce', '80177', 'http://commerce1-f.akamaihd.net'],
        ['csce', '75229', 'http://srs-f.akamaihd.net'],
        ['dpc', '76590', 'http://dpc-f.akamaihd.net'],
        ['energy', '76448', 'http://energy-f.akamaihd.net'],
        ['epw', '76478', 'http://epw-f.akamaihd.net'],
        ['ethics', '76449', 'http://ethics-f.akamaihd.net'],
        ['finance', '76450', 'http://finance-f.akamaihd.net'],
        ['foreign', '76451', 'http://foreign-f.akamaihd.net'],
        ['govtaff', '76453', 'http://govtaff-f.akamaihd.net'],
        ['help', '76452', 'http://help-f.akamaihd.net'],
        ['indian', '76455', 'http://indian-f.akamaihd.net'],
        ['intel', '76456', 'http://intel-f.akamaihd.net'],
        ['intlnarc', '76457', 'http://intlnarc-f.akamaihd.net'],
        ['jccic', '85180', 'http://jccic-f.akamaihd.net'],
        ['jec', '76458', 'http://jec-f.akamaihd.net'],
        ['judiciary', '76459', 'http://judiciary-f.akamaihd.net'],
        ['rpc', '76591', 'http://rpc-f.akamaihd.net'],
        ['rules', '76460', 'http://rules-f.akamaihd.net'],
        ['saa', '76489', 'http://srs-f.akamaihd.net'],
        ['smbiz', '76461', 'http://smbiz-f.akamaihd.net'],
        ['srs', '75229', 'http://srs-f.akamaihd.net'],
        ['uscc', '76487', 'http://srs-f.akamaihd.net'],
        ['vetaff', '76462', 'http://vetaff-f.akamaihd.net'],
        ['arch', '', 'http://ussenate-f.akamaihd.net/']
    ]
    _IE_NAME = 'senate.gov'
    _VALID_URL = r'https?://(?:www\.)?senate\.gov/isvp/?\?(?P<qs>.+)'
    _TESTS = [{
        'url': 'http://www.senate.gov/isvp/?comm=judiciary&type=live&stt=&filename=judiciary031715&auto_play=false&wmode=transparent&poster=http%3A%2F%2Fwww.judiciary.senate.gov%2Fthemes%2Fjudiciary%2Fimages%2Fvideo-poster-flash-fit.png',
        'info_dict': {
            'id': 'judiciary031715',
            'ext': 'mp4',
            'title': 'Integrated Senate Video Player',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)$',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.senate.gov/isvp/?type=live&comm=commerce&filename=commerce011514.mp4&auto_play=false',
        'info_dict': {
            'id': 'commerce011514',
            'ext': 'mp4',
            'title': 'Integrated Senate Video Player'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.senate.gov/isvp/?type=arch&comm=intel&filename=intel090613&hc_location=ufi',
        # checksum differs each time
        'info_dict': {
            'id': 'intel090613',
            'ext': 'mp4',
            'title': 'Integrated Senate Video Player'
        }
    }, {
        # From http://www.c-span.org/video/?96791-1
        'url': 'http://www.senate.gov/isvp?type=live&comm=banking&filename=banking012715',
        'only_matching': True,
    }]

    @staticmethod
    #returns url from an iframe
    def _search_iframe_url(webpage):
        mobj = re.search(
            r'''<iframe\b[^>]+\bsrc\s*=\s*(['"])(?P<url>https?://www\.senate\.gov/isvp/?\?(?:(?!\1)\S)+)''',
            webpage)
        if mobj:
            return mobj.group('url')

    # returns stream_number, stream_domain, stream_id, msl3
    def _get_info_for_comm(self, committee):
        return self._COMM_MAP[committee][0:]

    def _real_extract(self, url):
        # smuggled data may contain a forced title that should be used
        url, smuggled_data = unsmuggle_url(url, {})
        qs = compat_parse_qs(re.match(self._VALID_URL, url).group('qs'))

        # error handling for invalid URL - specify which error
        if not qs.get('filename'):
            raise ExtractorError('Invalid URL. Missing filename in query parameters', expected=True)
        if not qs.get('comm'):
            raise ExtractorError('Invalid URL. Missing committee in query parameters', expected=True)

        committee = qs.get('comm')[0]
        filename = qs.get('filename')[0]
        video_id = re.sub(r'\.mp4$', '', filename)

        # there is no point in pulling the title from the webpage since it always defaults to 'Integrated Senate Player'
        title = smuggled_data.get('force_title') or filename

        # extract more info about committee (for matching to possible locations)
        stream_number, stream_domain, stream_id, msl3 = self._get_info_for_comm(committee)

        # possible locations that m3u8 could be located at
        possible_manifest_urls = [
            'https://www-senate-gov-media-srs.akamaized.net/hls/live/%d/%s/%s/master.m3u8' % (stream_id, committee, filename),
            'https://www-senate-gov-msl3archive.akamaized.net/%s/%s_1/master.m3u8' % (msl3, filename),
            '{stream_domain}/i/%s_1@%d/master.m3u8' % (filename, stream_number),
            'https://ussenate-f.akamaihd.net/i/%s' % video_id,
        ]

        # iterate through possible locations until we find a match (match found when formats is filled)
        formats = []
        for url in possible_manifest_urls: 
            entries = self._extract_m3u8_formats(
                url, 
                video_id,
                ext='mp4',
                m3u8_id='hls',
                entry_protocal='mu38_native',
                fatal=False
            )

            for entry in entries:
                mobj = re.search(r'(?P<tag>-[pb]).m3u8', entry['url'])
                if mobj:
                    entry['format_id'] += mobj.group('tag')
                formats.append(entry)

            if formats:
                break
        
        self._sort_formats(formats)
        thumbnail = url_or_none(qs.get('poster', [None])[-1])
        start_time = parse_duration(qs.get('stt', [None])[-1])
        stop_time = parse_duration(qs.get('dur', [None])[-1])
        if stop_time is not None:
            stop_time += start_time or 0

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'start_time': start_time,
            'stop_time': stop_time,
        }
