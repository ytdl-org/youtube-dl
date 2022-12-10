# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unsmuggle_url,
)
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)


class SenateISVPIE(InfoExtractor):
    _COMM_MAP = {
        'ag':           [76440, 'https://ag-f.akamaihd.net',        2036803, 'agriculture'],
        'aging':        [76442, 'https://aging-f.akamaihd.net',     2036801, 'aging'],
        'approps':      [76441, 'https://approps-f.akamaihd.net',   2036802, 'appropriations'],
        'armed':        [76445, 'https://armed-f.akamaihd.net',     2036800, 'armedservices'],
        'banking':      [76446, 'https://banking-f.akamaihd.net',   2036799, 'banking'],
        'budget':       [76447, 'https://budget-f.akamaihd.net',    2036798, 'budget'],
        'cecc':         [76486, 'https://srs-f.akamaihd.net',       2036782, 'srs_cecc'],
        'commerce':     [80177, 'https://commerce1-f.akamaihd.net', 2036779, 'commerce'],
        'csce':         [75229, 'https://srs-f.akamaihd.net',       2036777, 'srs_srs'],
        'dpc':          [76590, 'https://dpc-f.akamaihd.net',       None, 'dpc'],
        'energy':       [76448, 'https://energy-f.akamaihd.net',    2036797, 'energy'],
        'epw':          [76478, 'https://epw-f.akamaihd.net',       2036783, 'environment'],
        'ethics':       [76449, 'https://ethics-f.akamaihd.net',    2036796, 'ethics'],
        'finance':      [76450, 'https://finance-f.akamaihd.net',   2036795, 'finance_finance'],
        'foreign':      [76451, 'https://foreign-f.akamaihd.net',   2036794, 'foreignrelations'],
        'govtaff':      [76453, 'https://govtaff-f.akamaihd.net',   2036792, 'hsgac'],
        'help':         [76452, 'https://help-f.akamaihd.net',      2036793, 'help'],
        'indian':       [76455, 'https://indian-f.akamaihd.net',    2036791, 'indianaffairs'],
        'intel':        [76456, 'https://intel-f.akamaihd.net',     2036790, 'intelligence'],
        'intlnarc':     [76457, 'https://intlnarc-f.akamaihd.net',  None, 'internationalnarcoticscaucus'],
        'jccic':        [85180, 'https://jccic-f.akamaihd.net',     2036778, 'jccic'],
        'jec':          [76458, 'https://jec-f.akamaihd.net',       2036789, 'jointeconomic'],
        'judiciary':    [76459, 'https://judiciary-f.akamaihd.net', 2036788,'judiciary'],
        'rpc':          [76591, 'https://rpc-f.akamaihd.net',       None, 'rpc'],
        'rules':        [76460, 'https://rules-f.akamaihd.net',     2036787, 'rules'],
        'saa':          [76489, 'https://srs-f.akamaihd.net',       2036780, 'srs_saa'],
        'smbiz':        [76461, 'https://smbiz-f.akamaihd.net',     2036786, 'smallbusiness'],
        'srs':          [75229, 'https://srs-f.akamaihd.net',       2031966, 'srs_srs'],
        'uscc':         [76487, 'https://srs-f.akamaihd.net',       2036781, 'srs_uscc'],
        'vetaff':       [76462, 'https://vetaff-f.akamaihd.net',    2036785, 'veteransaffairs'],
        'arch':         [None, 'https://ussenate-f.akamaihd.net/', None, None],
        'uscp':         [None, '', 2043685, None, 'uscp'],
        'cio':          [None, '', 2043686, None, 'cio'],
    }
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
    def _search_iframe_url(webpage):
        mobj = re.search(
            r"<iframe[^>]+src=['\"](?P<url>https?://www\.senate\.gov/isvp/?\?[^'\"]+)['\"]",
            webpage)
        if mobj:
            return mobj.group('url')

    def _get_info_for_comm(self, committee):
        for entry in self._COMM_MAP:
            if entry[0] == committee:
                return entry[1:]

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        qs = compat_parse_qs(re.match(self._VALID_URL, url).group('qs'))
        if not qs.get('filename') or not qs.get('type') or not qs.get('comm'):
            raise ExtractorError('Invalid URL', expected=True)

        video_id = re.sub(r'.mp4$', '', qs['filename'][0])

        webpage = self._download_webpage(url, video_id)

        if smuggled_data.get('force_title'):
            title = smuggled_data['force_title']
        else:
            title = self._html_search_regex(r'<title>([^<]+)</title>', webpage, video_id)
        poster = qs.get('poster')
        thumbnail = poster[0] if poster else None

        video_type = qs['type'][0]
        committee = video_type if video_type == 'arch' else qs['comm'][0]
        stream_num, domain = self._get_info_for_comm(committee)

        formats = []
        if video_type == 'arch':
            filename = video_id if '.' in video_id else video_id + '.mp4'
            formats = [{
                # All parameters in the query string are necessary to prevent a 403 error
                'url': compat_urlparse.urljoin(domain, filename) + '?v=3.1.0&fp=&r=&g=',
            }]
        else:
            hdcore_sign = 'hdcore=3.1.0'
            url_params = (domain, video_id, stream_num)
            f4m_url = '%s/z/%s_1@%s/manifest.f4m?' % url_params + hdcore_sign
            m3u8_url = '%s/i/%s_1@%s/master.m3u8' % url_params
            for entry in self._extract_f4m_formats(f4m_url, video_id, f4m_id='f4m'):
                # URLs without the extra param induce an 404 error
                entry.update({'extra_param_to_segment_url': hdcore_sign})
                formats.append(entry)
            for entry in self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4', m3u8_id='m3u8'):
                mobj = re.search(r'(?P<tag>(?:-p|-b)).m3u8', entry['url'])
                if mobj:
                    entry['format_id'] += mobj.group('tag')
                formats.append(entry)

            self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
