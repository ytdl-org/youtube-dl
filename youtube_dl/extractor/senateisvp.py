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
    # committee --> [stream_number, stream_domain, stream_id, msl3]
    _COMM_MAP = {
        'ag': [76440, 'https://ag-f.akamaihd.net', 2036803, 'agriculture'],
        'aging': [76442, 'https://aging-f.akamaihd.net', 2036801, 'aging'],
        'approps': [76441, 'https://approps-f.akamaihd.net', 2036802, 'appropriations'],
        'armed': [76445, 'https://armed-f.akamaihd.net', 2036800, 'armedservices'],
        'banking': [76446, 'https://banking-f.akamaihd.net', 2036799, 'banking'],
        'budget': [76447, 'https://budget-f.akamaihd.net', 2036798, 'budget'],
        'cecc': [76486, 'https://srs-f.akamaihd.net', 2036782, 'srs_cecc'],
        'commerce': [80177, 'https://commerce1-f.akamaihd.net', 2036779, 'commerce'],
        'csce': [75229, 'https://srs-f.akamaihd.net', 2036777, 'srs_srs'],
        'dpc': [76590, 'https://dpc-f.akamaihd.net', None, 'dpc'],
        'energy': [76448, 'https://energy-f.akamaihd.net', 2036797, 'energy'],
        'epw': [76478, 'https://epw-f.akamaihd.net', 2036783, 'environment'],
        'ethics': [76449, 'https://ethics-f.akamaihd.net', 2036796, 'ethics'],
        'finance': [76450, 'https://finance-f.akamaihd.net', 2036795, 'finance_finance'],
        'foreign': [76451, 'https://foreign-f.akamaihd.net', 2036794, 'foreignrelations'],
        'govtaff': [76453, 'https://govtaff-f.akamaihd.net', 2036792, 'hsgac'],
        'help': [76452, 'https://help-f.akamaihd.net', 2036793, 'help'],
        'indian': [76455, 'https://indian-f.akamaihd.net', 2036791, 'indianaffairs'],
        'intel': [76456, 'https://intel-f.akamaihd.net', 2036790, 'intelligence'],
        'intlnarc': [76457, 'https://intlnarc-f.akamaihd.net', None, 'internationalnarcoticscaucus'],
        'jccic': [85180, 'https://jccic-f.akamaihd.net', 2036778, 'jccic'],
        'jec': [76458, 'https://jec-f.akamaihd.net', 2036789, 'jointeconomic'],
        'judiciary': [76459, 'https://judiciary-f.akamaihd.net', 2036788, 'judiciary'],
        'rpc': [76591, 'https://rpc-f.akamaihd.net', None, 'rpc'],
        'rules': [76460, 'https://rules-f.akamaihd.net', 2036787, 'rules'],
        'saa': [76489, 'https://srs-f.akamaihd.net', 2036780, 'srs_saa'],
        'smbiz': [76461, 'https://smbiz-f.akamaihd.net', 2036786, 'smallbusiness'],
        'srs': [75229, 'https://srs-f.akamaihd.net', 2031966, 'srs_srs'],
        'uscc': [76487, 'https://srs-f.akamaihd.net', 2036781, 'srs_uscc'],
        'vetaff': [76462, 'https://vetaff-f.akamaihd.net', 2036785, 'veteransaffairs'],
        'arch': [None, 'https://ussenate-f.akamaihd.net/', None, None],
        'uscp': [None, '', 2043685, 'uscp'],
        'cio': [None, '', 2043686, 'cio'],
    }

    _IE_NAME = 'senate.gov'
    _VALID_URL = r'https?://(?:www\.)?senate\.gov/isvp/?\?(?P<qs>.+)'
    _TESTS = [{
        'url': 'http://www.senate.gov/isvp/?comm=judiciary&type=live&stt=&filename=judiciary031715&auto_play=false&wmode=transparent&poster=http%3A%2F%2Fwww.judiciary.senate.gov%2Fthemes%2Fjudiciary%2Fimages%2Fvideo-poster-flash-fit.png',
        'info_dict': {
            'id': 'judiciary031715',
            'ext': 'mp4',
            'title': 'judiciary031715',
            'thumbnail': 'http://www.judiciary.senate.gov/themes/judiciary/images/video-poster-flash-fit.png',
        },
        'expected_warnings': ['Failed to download m3u8 information: HTTP Error 404: Not Found'],
    }, {
        'url': 'http://www.senate.gov/isvp/?type=arch&comm=intel&filename=intel090613&hc_location=ufi',
        'info_dict': {
            'id': 'intel090613',
            'ext': 'mp4',
            'title': 'intel090613',
        },
        'expected_warnings': ['Failed to download m3u8 information: HTTP Error 404: Not Found'],
    }, {
        'url': 'https://www.senate.gov/isvp/?comm=govtaff&type=archv&stt=975&filename=govtaff111722&auto_play=false&poster=https%3A%2F%2Fwww%2Ehsgac%2Esenate%2Egov%2Fimages%2Fvideo%2Dposter%2Dflash%2Dfit%2Epng',
        'info_dict': {
            'id': 'govtaff111722',
            'ext': 'mp4',
            'title': 'govtaff111722',
            'thumbnail': 'https://www.hsgac.senate.gov/images/video-poster-flash-fit.png',
        },
    }, {
        'url': 'https://www.senate.gov/isvp/?type=arch&comm=energy&filename=energy111722&stt=00:22:30&auto_play=false&wmode=transparent&poster=https%3A%2F%2Fwww%2Eenergy%2Esenate%2Egov%2Fthemes%2Fenergy%2Fimages%2Fvideo%2Dposter%2Dflash%2Dfit%2Epng',
        'info_dict': {
            'id': 'energy111722',
            'ext': 'mp4',
            'title': 'energy111722',
            'thumbnail': 'https://www.energy.senate.gov/themes/energy/images/video-poster-flash-fit.png',
        },
    }, {
        'url': 'https://www.senate.gov/isvp/?comm=foreign&type=archv&stt=0&filename=foreign080322&auto_play=false&wmode=transparent&poster=https%3A%2F%2Fwww%2Eforeign%2Esenate%2Egov%2Fthemes%2Fforeign%2Fimages%2Fvideo%2Dposter%2Dflash%2Dfit%2Epng',
        'info_dict': {
            'id': 'foreign080322',
            'ext': 'mp4',
            'title': 'foreign080322',
            'thumbnail': 'https://www.foreign.senate.gov/themes/foreign/images/video-poster-flash-fit.png',
        },
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
                entry_protocol='mu38_native',
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
