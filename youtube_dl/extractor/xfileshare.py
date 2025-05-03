# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_chr,
    compat_zip as zip,
)
from ..utils import (
    clean_html,
    decode_packed_codes,
    determine_ext,
    extract_attributes,
    ExtractorError,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    merge_dicts,
    T,
    traverse_obj,
    url_or_none,
    urlencode_postdata,
)


# based on openload_decode from 2bfeee69b976fe049761dd3012e30b637ee05a58
def aa_decode(aa_code):
    symbol_table = (
        ('7', '((ﾟｰﾟ) + (o^_^o))'),
        ('6', '((o^_^o) +(o^_^o))'),
        ('5', '((ﾟｰﾟ) + (ﾟΘﾟ))'),
        ('2', '((o^_^o) - (ﾟΘﾟ))'),
        ('4', '(ﾟｰﾟ)'),
        ('3', '(o^_^o)'),
        ('1', '(ﾟΘﾟ)'),
        ('0', '(c^_^o)'),
        ('+', ''),
    )
    delim = '(ﾟДﾟ)[ﾟεﾟ]+'

    def chr_from_code(c):
        for val, pat in symbol_table:
            c = c.replace(pat, val)
        if c.startswith(('u', 'U')):
            base = 16
            c = c[1:]
        else:
            base = 10
        c = int_or_none(c, base=base)
        return '' if c is None else compat_chr(c)

    return ''.join(
        chr_from_code(aa_char)
        for aa_char in aa_code.split(delim))


class XFileShareIE(InfoExtractor):
    _SITES = (
        # status check 2024-10: site availability, G site: search
        (r'aparat\.cam', 'Aparat'),  # Cloudflare says host error 522, apparently changed to wolfstream.tv
        (r'filemoon\.(?:sx|to|in)', 'FileMoon'),
        # (r'gounlimited\.to', 'GoUnlimited'),  # domain not found
        (r'govid\.me', 'GoVid'),  # no media pages listed
        (r'highstream\.tv', 'HighStream'),  # Cloudflare says host error 522, clipwatching.com now dead
        (r'holavid\.com', 'HolaVid'),  # hoster default home page
        # (r'streamty\.com', 'Streamty'),  # spam parking domain
        # (r'thevideobee\.to', 'TheVideoBee'),  # domain for sale
        (r'uqload\.ws', 'Uqload'),  # .com, .co, .to redirect here
        # (r'(vadbam.net', 'VadBam'),  # domain not found
        (r'(?:vedbam\.xyz|vadbam\.net|vbn\d\.vdbtm\.shop)', 'V?dB?m'),  # vidbom.com redirects here, but no valid media pages listed
        (r'vidlo\.us', 'vidlo'),  # no valid media pages listed
        (r'vidlocker\.xyz', 'VidLocker'),  # no media pages listed
        (r'(?:w\d\.)?viidshar\.com', 'VidShare'),  # vidshare.tv parked
        # (r'vup\.to', 'VUp'),  # domain not found
        # (r'wolfstream\.tv', 'WolfStream'),  # domain not found
        (r'xvideosharing\.com', 'XVideoSharing'),
    )

    IE_DESC = 'XFileShare-based sites: %s' % ', '.join(list(zip(*_SITES))[1])
    _VALID_URL = (r'https?://(?:www\.)?(?P<host>%s)/(?P<sub>[a-z]/|)(?:embed-)?(?P<id>[0-9a-zA-Z]+)'
                  % '|'.join(site for site in list(zip(*_SITES))[0]))
    _EMBED_REGEX = [r'<iframe\b[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//(?:%s)/embed-[0-9a-zA-Z]+.*?)\1' % '|'.join(site for site in list(zip(*_SITES))[0])]

    _FILE_NOT_FOUND_REGEXES = (
        r'>\s*(?:404 - )?File Not Found\s*<',
        r'>\s*The file was removed by administrator\s*<',
    )
    _TITLE_REGEXES = (
        r'style="z-index: [0-9]+;">([^<]+)</span>',
        r'<td nowrap>([^<]+)</td>',
        r'h4-fine[^>]*>([^<]+)<',
        r'>Watch (.+?)(?: mp4)?(?: The Ultimate Free Video Hosting Solution for Webmasters and Bloggers)?<',
        r'<h2 class="video-page-head">([^<]+)</h2>',
        r'<h2 style="[^"]*color:#403f3d[^"]*"[^>]*>([^<]+)<',  # streamin.to (dead)
        r'title\s*:\s*"([^"]+)"',  # govid.me
    )
    _SOURCE_URL_REGEXES = (
        r'(?:file|src)\s*:\s*(["\'])(?P<url>http(?:(?!\1).)+\.(?:m3u8|mp4|flv)(?:(?!\1).)*)\1',
        r'file_link\s*=\s*(["\'])(?P<url>http(?:(?!\1).)+)\1',
        r'addVariable\((\\?["\'])file\1\s*,\s*(\\?["\'])(?P<url>http(?:(?!\2).)+)\2\)',
        r'<embed[^>]+src=(["\'])(?P<url>http(?:(?!\1).)+\.(?:m3u8|mp4|flv)(?:(?!\1).)*)\1',
    )
    _THUMBNAIL_REGEXES = (
        r'<video[^>]+poster="([^"]+)"',
        r'(?:image|poster)\s*:\s*["\'](http[^"\']+)["\'],',
    )

    _TESTS = [{
        'note': 'link in `sources`',
        'url': 'https://uqload.ws/4sah252totrk.html',
        'md5': '1f11151b5044862fbc3c112732f9f7d8',
        'info_dict': {
            'id': '4sah252totrk',
            'ext': 'mp4',
            'title': 'JEONGHAN WONWOO Interview With Allure Korea Arabic Sub',
            'thumbnail': r're:https://.*\.jpg'
        },
        'params': {
            'nocheckcertificate': True,
        },
        # 'expected_warnings': ['Unable to extract JWPlayer data'],
    }, {
        'note': 'link in Playerjs',  # need test with 'link in decoded `sources`'
        'url': 'https://xvideosharing.com/8cnupzc1z8xq.html',
        'md5': '9725ca7229e8f3046f2417da3bd5eddc',
        'info_dict': {
            'id': '8cnupzc1z8xq',
            'ext': 'mp4',
            'title': 'HEVC X265 Big Buck Bunny 1080 10s 20MB',
            'thumbnail': r're:https?://.*\.jpg',
        },
    }, {
        'note': 'JWPlayer link in un-p,a,c,k,e,d JS, in player frame',
        'url': 'https://filemoon.sx/d/fbsxidybremo',
        'md5': '82007a71661630f60e866f0d6ed31b2a',
        'info_dict': {
            'id': 'fbsxidybremo',
            'title': 'Uchouten',
            'ext': 'mp4'
        },
        'params': {
            'skip_download': 'ffmpeg',
        },
        'expected_warnings': ['hlsnative has detected features it does not support'],
    }, {
        'note': 'JWPlayer link in un-p,a,c,k,e,d JS',
        'url': 'https://vadbam.net/6lnbkci96wly.html',
        'md5': 'a1616800076177e2ac769203957c54bc',
        'info_dict': {
            'id': '6lnbkci96wly',
            'title': 'Heart Crime S01 E03 weciima autos',
            'ext': 'mp4'
        },
    }, {
        'note': 'JWPlayer link in clear',
        'url': 'https://w1.viidshar.com/nnibe0xf0h79.html',
        'md5': 'b95b97978093bc287c322307c689bd94',
        'info_dict': {
            'id': 'nnibe0xf0h79',
            'title': 'JaGa 68ar',
            'ext': 'mp4'
        },
        'params': {
            'skip_download': 'ffmpeg',
        },
        'expected_warnings': ['hlsnative has detected features it does not support'],
    }, {
        'url': 'https://aparat.cam/n4d6dh0wvlpr',
        'only_matching': True,
    }, {
        'url': 'https://highstream.tv/2owiyz3sjoux',
        'only_matching': True,
    }, {
        'url': 'https://vedbam.xyz/6lnbkci96wly.html',
        'only_matching': True,
    }, {
        'url': 'https://vbn2.vdbtm.shop/6lnbkci96wly.html',
        'only_matching': True,
    }, {
        'url': 'https://filemoon.in/e/5abn1ze9jifb',
        'only_matching': True,
    }]

    @classmethod
    def _extract_urls(cls, webpage):

        def yield_urls():
            for regex in cls._EMBED_REGEX:
                for mobj in re.finditer(regex, webpage):
                    yield mobj.group('url')

        return list(yield_urls())

    def _real_extract(self, url):
        host, sub, video_id = self._match_valid_url(url).group('host', 'sub', 'id')

        url = 'https://%s/%s%s' % (
            host, sub,
            'embed-%s.html' % video_id if host in ('govid.me', 'vidlo.us') else video_id)
        webpage = self._download_webpage(url, video_id)
        main = self._search_regex(
            r'(?s)<main>(.+)</main>', webpage, 'main', default=webpage)
        container_div = (
            get_element_by_id('container', main)
            or get_element_by_class('container', main)
            or webpage)
        if self._search_regex(
                r'>This server is in maintenance mode\.', container_div,
                'maint error', group=0, default=None):
            raise ExtractorError(clean_html(container_div), expected=True)
        if self._search_regex(
                'not available in your country', container_div,
                'geo block', group=0, default=None):
            self.raise_geo_restricted()
        if self._search_regex(
                self._FILE_NOT_FOUND_REGEXES, container_div,
                'missing video error', group=0, default=None):
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        fields = self._hidden_inputs(webpage)

        if fields.get('op') == 'download1':
            countdown = int_or_none(self._search_regex(
                r'<span id="countdown_str">(?:[Ww]ait)?\s*<span id="cxc">(\d+)</span>\s*(?:seconds?)?</span>',
                webpage, 'countdown', default=None))
            if countdown:
                self._sleep(countdown, video_id)

            webpage = self._download_webpage(
                url, video_id, 'Downloading video page',
                data=urlencode_postdata(fields), headers={
                    'Referer': url,
                    'Content-type': 'application/x-www-form-urlencoded',
                })

        title = (
            self._search_regex(self._TITLE_REGEXES, webpage, 'title', default=None)
            or self._og_search_title(webpage, default='')).strip()

        def deobfuscate(html):
            for regex, func in (
                    (r'(?s)(?<!-)\b(eval\(function\(p,a,c,k,e,d\)\{(?:(?!</script>).)+\)\))',
                     decode_packed_codes),
                    (r'(ﾟ.+)', aa_decode)):
                obf_code = self._search_regex(regex, html, 'obfuscated code', default=None)
                if obf_code:
                    return html.replace(obf_code, func(obf_code))

        def jw_extract(html):
            jwplayer_data = self._find_jwplayer_data(
                html.replace(r'\'', '\''), video_id)
            result = self._parse_jwplayer_data(
                jwplayer_data, video_id, require_title=False,
                m3u8_id='hls', mpd_id='dash')
            result = traverse_obj(result, (
                (None, ('entries', 0)), T(lambda r: r if r['formats'] else None)),
                get_all=False) or {}
            if not result and jwplayer_data:
                self.report_warning(
                    'Failed to extract JWPlayer formats', video_id=video_id)
            return result

        def extract_from_links(html):
            urls = set()
            for regex in self._SOURCE_URL_REGEXES:
                for mobj in re.finditer(regex, html):
                    urls.add(mobj.group('url'))

            sources = self._search_json(
                r'\bsources\s*:', webpage, 'sources', video_id,
                contains_pattern=r'\[(?!{)[^\]]+\]', default=[])
            urls.update(sources)

            formats = []
            for video_url in traverse_obj(urls, (Ellipsis, T(url_or_none))):
                if determine_ext(video_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                else:
                    formats.append({
                        'url': video_url,
                        'format_id': 'sd',
                    })
            return {'formats': formats}

        def extract_info(html):
            html = deobfuscate(html) or html
            result = jw_extract(html)
            if not result.get('formats'):
                result = extract_from_links(html)
            return result

        def pages_to_extract(html):
            yield html
            # page with separate protected download page also has player link
            player_iframe = self._search_regex(
                r'(<iframe\s[^>]+>)',
                get_element_by_id('iframe-holder', html) or '',
                'player iframe', default='')
            player_url = extract_attributes(player_iframe).get('src')
            if player_url:
                html = self._download_webpage(player_url, video_id, note='Downloading player page', fatal=False)
            if html:
                yield html

        result = {}
        for html in pages_to_extract(webpage):
            result = extract_info(html)
            if result.get('formats'):
                break

        self._sort_formats(result['formats'])

        thumbnail = self._search_regex(
            self._THUMBNAIL_REGEXES, webpage, 'thumbnail', default=None)

        if not (title or result.get('title')):
            title = self._generic_title(url) or video_id

        return merge_dicts(result, {
            'id': video_id,
            'title': title or None,
            'thumbnail': thumbnail,
            'http_headers': {'Referer': url}
        })
