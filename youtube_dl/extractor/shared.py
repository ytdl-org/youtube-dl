from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_b64decode,
    compat_urllib_parse_unquote_plus
)
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    KNOWN_EXTENSIONS,
    parse_filesize,
    url_or_none,
    urlencode_postdata,
    rot47
)


class SharedBaseIE(InfoExtractor):
    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage, urlh = self._download_webpage_handle(url, video_id)

        if self._FILE_NOT_FOUND in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

        video_url = self._extract_video_url(webpage, video_id, url)

        title = self._extract_title(webpage)
        filesize = int_or_none(self._extract_filesize(webpage))

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'filesize': filesize,
            'title': title,
        }

    def _extract_title(self, webpage):
        return compat_b64decode(self._html_search_meta(
            'full:title', webpage, 'title')).decode('utf-8')

    def _extract_filesize(self, webpage):
        return self._html_search_meta(
            'full:size', webpage, 'file size', fatal=False)


class SharedIE(SharedBaseIE):
    IE_DESC = 'shared.sx'
    _VALID_URL = r'https?://shared\.sx/(?P<id>[\da-z]{10})'
    _FILE_NOT_FOUND = '>File does not exist<'

    _TEST = {
        'url': 'http://shared.sx/0060718775',
        'md5': '106fefed92a8a2adb8c98e6a0652f49b',
        'info_dict': {
            'id': '0060718775',
            'ext': 'mp4',
            'title': 'Bmp4',
            'filesize': 1720110,
        },
    }

    def _extract_video_url(self, webpage, video_id, url):
        download_form = self._hidden_inputs(webpage)

        video_page = self._download_webpage(
            url, video_id, 'Downloading video page',
            data=urlencode_postdata(download_form),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url,
            })

        video_url = self._html_search_regex(
            r'data-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
            video_page, 'video URL', group='url')

        return video_url


class VivoIE(SharedBaseIE):
    IE_DESC = 'vivo.sx'
    _VALID_URL = r'https?://vivo\.sx/(?P<id>[\da-z]{10})'
    _FILE_NOT_FOUND = '>The file you have requested does not exists or has been removed'

    _TEST = {
        'url': 'https://vivo.sx/5ec5b4cd00',
        'md5': 'b95282602513086f5b71aae4cd043a0c',
        'info_dict': {
            'id': '5ec5b4cd00',
            'ext': 'mp4',
            'title': 'big_buck_bunny_480p_surround-fix',
            'filesize': 68270000,
        },
    }

    def _extract_title(self, webpage):
        title = self._html_search_regex(
            r'data-name\s*=\s*(["\'])(?P<title>(?:(?!\1).)+)\1', webpage,
            'title', default=None, group='title')
        if title:
            ext = determine_ext(title)
            if ext.lower() in KNOWN_EXTENSIONS:
                title = title.rpartition('.' + ext)[0]
            return title
        return self._og_search_title(webpage)

    def _extract_filesize(self, webpage):
        return parse_filesize(self._search_regex(
            r'data-type=["\']video["\'][^>]*>Watch.*?<strong>\s*\((.+?)\)',
            webpage, 'filesize', fatal=False))

    def _extract_video_url(self, webpage, video_id, url):
        def decode_url(encoded_url):
            return rot47(compat_urllib_parse_unquote_plus(encoded_url))

        stream_url = self._search_regex(
            r'InitializeStream\s*\(\{[\s\S]*(source\:[\s]\')(?P<url>[\s\S\:]+?)(\',\s*)', webpage,
            'stream url', default=None, group='url')

        if stream_url:
            return url_or_none(decode_url(stream_url))
        return None
