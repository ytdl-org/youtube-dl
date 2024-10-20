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
        # status check 2024-02: site availability, G site: search
        (r'aparat\.cam', 'Aparat'),  # Cloudflare says host error 522, apparently changed to wolfstreeam.tv
        (r'filemoon\.sx/.', 'FileMoon'),
        (r'gounlimited\.to', 'GoUnlimited'),  # no media pages listed
        (r'govid\.me', 'GoVid'),  # no media pages listed
        (r'highstream\.tv', 'HighStream'),  # clipwatching.com redirects here
        (r'holavid\.com', 'HolaVid'),  # Cloudflare says host error 522
        # (r'streamty\.com', 'Streamty'),  # no media pages listed, connection timeout
        # (r'thevideobee\.to', 'TheVideoBee'),  # no pages listed, refuses connection
        (r'uqload\.to', 'Uqload'),  # .com, .co redirect here
        (r'(?:vedbam\.xyz|vadbam.net)', 'V?dB?m'),  # vidbom.com redirects here, but no valid media pages listed
        (r'vidlo\.us', 'vidlo'),  # no valid media pages listed
        (r'vidlocker\.xyz', 'VidLocker'),  # no media pages listed
        (r'(?:w\d\.)?viidshar\.com', 'VidShare'),  # vidshare.tv redirects here
        # (r'vup\.to', 'VUp'),  # domain not found
        (r'wolfstream\.tv', 'WolfStream'),
        (r'xvideosharing\.com', 'XVideoSharing'),  # just started showing 'maintenance mode'
    )

    IE_DESC = 'XFileShare-based sites: %s' % ', '.join(list(zip(*_SITES))[1])
    _VALID_URL = (r'https?://(?:www\.)?(?P<host>%s)/(?:embed-)?(?P<id>[0-9a-zA-Z]+)'
                  % '|'.join(site for site in list(zip(*_SITES))[0]))
    _EMBED_REGEX = [r'<iframe\b[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//(?:%s)/embed-[0-9a-zA-Z]+.*?)\1' % '|'.join(site for site in list(zip(*_SITES))[0])]

    _FILE_NOT_FOUND_REGEXES = (
        r'>(?:404 - )?File Not Found<',
        r'>The file was removed by administrator<',
    )
    _TITLE_REGEXES = (
        r'style="z-index: [0-9]+;">([^<]+)</span>',
        r'<td nowrap>([^<]+)</td>',
        r'h4-fine[^>]*>([^<]+)<',
        r'>Watch (.+)[ <]',
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
        'url': 'https://uqload.to/dcsu06gdb45o',
        'md5': '7f8db187b254379440bf4fcad094ae86',
        'info_dict': {
            'id': 'dcsu06gdb45o',
            'ext': 'mp4',
            'title': 'f2e31015957e74c8c8427982e161c3fc mp4',
            'thumbnail': r're:https://.*\.jpg'
        },
        'params': {
            'nocheckcertificate': True,
        },
        'expected_warnings': ['Unable to extract JWPlayer data'],
    }, {
        'note': 'link in decoded `sources`',
        'url': 'https://xvideosharing.com/1tlg6agrrdgc',
        'md5': '2608ce41932c1657ae56258a64e647d9',
        'info_dict': {
            'id': '1tlg6agrrdgc',
            'ext': 'mp4',
            'title': '0121',
            'thumbnail': r're:https?://.*\.jpg',
        },
        'skip': 'This server is in maintenance mode.',
    }, {
        'note': 'JWPlayer link in un-p,a,c,k,e,d JS',
        'url': 'https://filemoon.sx/e/dw40rxrzruqz',
        'md5': '5a713742f57ac4aef29b74733e8dda01',
        'info_dict': {
            'id': 'dw40rxrzruqz',
            'title': 'dw40rxrzruqz',
            'ext': 'mp4'
        },
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
        'md5': 'f0a580ce9df06cc61b4a5c979d672367',
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
        'note': 'JWPlayer link in clear',
        'url': 'https://wolfstream.tv/a3drtehyrg52.html',
        'md5': '1901d86a79c5e0c6a51bdc9a4cfd3769',
        'info_dict': {
            'id': 'a3drtehyrg52',
            'title': 'NFL 2023 W04 DET@GB',
            'ext': 'mp4'
        },
    }, {
        'url': 'https://aparat.cam/n4d6dh0wvlpr',
        'only_matching': True,
    }, {
        'url': 'https://uqload.to/ug5somm0ctnk.html',
        'only_matching': True,
    }, {
        'url': 'https://highstream.tv/2owiyz3sjoux',
        'only_matching': True,
    }, {
        'url': 'https://vedbam.xyz/6lnbkci96wly.html',
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
        host, video_id = self._match_valid_url(url).group('host', 'id')

        url = 'https://%s/%s' % (
            host,
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
            or self._og_search_title(webpage, default=None)
            or video_id).strip()

        obf_code = True
        while obf_code:
            for regex, func in (
                    (r'(?s)(?<!-)\b(eval\(function\(p,a,c,k,e,d\)\{(?:(?!</script>).)+\)\))',
                     decode_packed_codes),
                    (r'(ﾟ.+)', aa_decode)):
                obf_code = self._search_regex(regex, webpage, 'obfuscated code', default=None)
                if obf_code:
                    webpage = webpage.replace(obf_code, func(obf_code))
                    break

        jwplayer_data = self._find_jwplayer_data(
            webpage.replace(r'\'', '\''), video_id)
        result = self._parse_jwplayer_data(
            jwplayer_data, video_id, require_title=False,
            m3u8_id='hls', mpd_id='dash')

        if not traverse_obj(result, 'formats'):
            if jwplayer_data:
                self.report_warning(
                    'Failed to extract JWPlayer formats', video_id=video_id)
            urls = set()
            for regex in self._SOURCE_URL_REGEXES:
                for mobj in re.finditer(regex, webpage):
                    urls.add(mobj.group('url'))

            sources = self._search_regex(
                r'sources\s*:\s*(\[(?!{)[^\]]+\])', webpage, 'sources', default=None)
            urls.update(traverse_obj(sources, (T(lambda s: self._parse_json(s, video_id)), Ellipsis)))

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
            result = {'formats': formats}

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
