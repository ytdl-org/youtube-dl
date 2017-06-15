# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    decode_packed_codes,
    determine_ext,
    ExtractorError,
    int_or_none,
    NO_DEFAULT,
    urlencode_postdata,
)


class XFileShareIE(InfoExtractor):
    _SITES = (
        (r'daclips\.(?:in|com)', 'DaClips'),
        (r'filehoot\.com', 'FileHoot'),
        (r'gorillavid\.(?:in|com)', 'GorillaVid'),
        (r'movpod\.in', 'MovPod'),
        (r'powerwatch\.pw', 'PowerWatch'),
        (r'rapidvideo\.ws', 'Rapidvideo.ws'),
        (r'thevideobee\.to', 'TheVideoBee'),
        (r'vidto\.me', 'Vidto'),
        (r'streamin\.to', 'Streamin.To'),
        (r'xvidstage\.com', 'XVIDSTAGE'),
        (r'vidabc\.com', 'Vid ABC'),
        (r'vidbom\.com', 'VidBom'),
        (r'vidlo\.us', 'vidlo'),
        (r'rapidvideo\.(?:cool|org)', 'RapidVideo.TV'),
        (r'fastvideo\.me', 'FastVideo.me'),
    )

    IE_DESC = 'XFileShare based sites: %s' % ', '.join(list(zip(*_SITES))[1])
    _VALID_URL = (r'https?://(?P<host>(?:www\.)?(?:%s))/(?:embed-)?(?P<id>[0-9a-zA-Z]+)'
                  % '|'.join(site for site in list(zip(*_SITES))[0]))

    _FILE_NOT_FOUND_REGEXES = (
        r'>(?:404 - )?File Not Found<',
        r'>The file was removed by administrator<',
    )

    _TESTS = [{
        'url': 'http://gorillavid.in/06y9juieqpmi',
        'md5': '5ae4a3580620380619678ee4875893ba',
        'info_dict': {
            'id': '06y9juieqpmi',
            'ext': 'mp4',
            'title': 'Rebecca Black My Moment Official Music Video Reaction-6GK87Rc8bzQ',
            'thumbnail': r're:http://.*\.jpg',
        },
    }, {
        'url': 'http://gorillavid.in/embed-z08zf8le23c6-960x480.html',
        'only_matching': True,
    }, {
        'url': 'http://daclips.in/3rso4kdn6f9m',
        'md5': '1ad8fd39bb976eeb66004d3a4895f106',
        'info_dict': {
            'id': '3rso4kdn6f9m',
            'ext': 'mp4',
            'title': 'Micro Pig piglets ready on 16th July 2009-bG0PdrCdxUc',
            'thumbnail': r're:http://.*\.jpg',
        }
    }, {
        'url': 'http://movpod.in/0wguyyxi1yca',
        'only_matching': True,
    }, {
        'url': 'http://filehoot.com/3ivfabn7573c.html',
        'info_dict': {
            'id': '3ivfabn7573c',
            'ext': 'mp4',
            'title': 'youtube-dl test video \'äBaW_jenozKc.mp4.mp4',
            'thumbnail': r're:http://.*\.jpg',
        },
        'skip': 'Video removed',
    }, {
        'url': 'http://vidto.me/ku5glz52nqe1.html',
        'info_dict': {
            'id': 'ku5glz52nqe1',
            'ext': 'mp4',
            'title': 'test'
        }
    }, {
        'url': 'http://powerwatch.pw/duecjibvicbu',
        'info_dict': {
            'id': 'duecjibvicbu',
            'ext': 'mp4',
            'title': 'Big Buck Bunny trailer',
        },
    }, {
        'url': 'http://xvidstage.com/e0qcnl03co6z',
        'info_dict': {
            'id': 'e0qcnl03co6z',
            'ext': 'mp4',
            'title': 'Chucky Prank 2015.mp4',
        },
    }, {
        # removed by administrator
        'url': 'http://xvidstage.com/amfy7atlkx25',
        'only_matching': True,
    }, {
        'url': 'http://vidabc.com/i8ybqscrphfv',
        'info_dict': {
            'id': 'i8ybqscrphfv',
            'ext': 'mp4',
            'title': 're:Beauty and the Beast 2017',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.rapidvideo.cool/b667kprndr8w',
        'only_matching': True,
    }, {
        'url': 'http://www.fastvideo.me/k8604r8nk8sn/FAST_FURIOUS_8_-_Trailer_italiano_ufficiale.mp4.html',
        'only_matching': True
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://%s/%s' % (mobj.group('host'), video_id)
        webpage = self._download_webpage(url, video_id)

        if any(re.search(p, webpage) for p in self._FILE_NOT_FOUND_REGEXES):
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        fields = self._hidden_inputs(webpage)

        if fields['op'] == 'download1':
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

        title = (self._search_regex(
            (r'style="z-index: [0-9]+;">([^<]+)</span>',
             r'<td nowrap>([^<]+)</td>',
             r'h4-fine[^>]*>([^<]+)<',
             r'>Watch (.+) ',
             r'<h2 class="video-page-head">([^<]+)</h2>',
             r'<h2 style="[^"]*color:#403f3d[^"]*"[^>]*>([^<]+)<'),  # streamin.to
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None) or video_id).strip()

        def extract_formats(default=NO_DEFAULT):
            urls = []
            for regex in (
                    r'file\s*:\s*(["\'])(?P<url>http(?:(?!\1).)+\.(?:m3u8|mp4|flv)(?:(?!\1).)*)\1',
                    r'file_link\s*=\s*(["\'])(?P<url>http(?:(?!\1).)+)\1',
                    r'addVariable\((\\?["\'])file\1\s*,\s*(\\?["\'])(?P<url>http(?:(?!\2).)+)\2\)',
                    r'<embed[^>]+src=(["\'])(?P<url>http(?:(?!\1).)+\.(?:m3u8|mp4|flv)(?:(?!\1).)*)\1'):
                for mobj in re.finditer(regex, webpage):
                    video_url = mobj.group('url')
                    if video_url not in urls:
                        urls.append(video_url)
            formats = []
            for video_url in urls:
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
            if not formats and default is not NO_DEFAULT:
                return default
            self._sort_formats(formats)
            return formats

        formats = extract_formats(default=None)

        if not formats:
            webpage = decode_packed_codes(self._search_regex(
                r"(}\('(.+)',(\d+),(\d+),'[^']*\b(?:file|embed)\b[^']*'\.split\('\|'\))",
                webpage, 'packed code'))
            formats = extract_formats()

        thumbnail = self._search_regex(
            r'image\s*:\s*["\'](http[^"\']+)["\'],', webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
