from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    ExtractorError,
)


class XHamsterIE(InfoExtractor):
    """Information Extractor for xHamster"""
    _VALID_URL = r'(?:http://)?(?:www\.)?xhamster\.com/movies/(?P<id>[0-9]+)/(?P<seo>.+?)\.html(?:\?.*)?'
    _TESTS = [{
        'url': 'http://xhamster.com/movies/1509445/femaleagent_shy_beauty_takes_the_bait.html',
        'file': '1509445.mp4',
        'md5': '8281348b8d3c53d39fffb377d24eac4e',
        'info_dict': {
            "upload_date": "20121014",
            "uploader_id": "Ruseful2011",
            "title": "FemaleAgent Shy beauty takes the bait",
            "age_limit": 18,
        }
    },
    {
        'url': 'http://xhamster.com/movies/2221348/britney_spears_sexy_booty.html?hd',
        'file': '2221348.flv',
        'md5': 'e767b9475de189320f691f49c679c4c7',
        'info_dict': {
            "upload_date": "20130914",
            "uploader_id": "jojo747400",
            "title": "Britney Spears  Sexy Booty",
            "age_limit": 18,
        }
    }]

    def _real_extract(self,url):
        def extract_video_url(webpage):
            mobj = re.search(r'\'srv\': \'(?P<server>[^\']*)\',\s*\'file\': \'(?P<file>[^\']+)\',', webpage)
            if mobj is None:
                raise ExtractorError('Unable to extract media URL')
            if len(mobj.group('server')) == 0:
                return compat_urllib_parse.unquote(mobj.group('file'))
            else:
                return mobj.group('server')+'/key='+mobj.group('file')

        def extract_mp4_video_url(webpage):
            mp4 = re.search(r'<a href=\"(.+?)\" class=\"mp4Play\"',webpage)
            if mp4 is None:
                return None
            else:
                return mp4.group(1)

        def is_hd(webpage):
            return '<div class=\'icon iconHD\'' in webpage

        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        seo = mobj.group('seo')
        mrss_url = 'http://xhamster.com/movies/%s/%s.html' % (video_id, seo)
        webpage = self._download_webpage(mrss_url, video_id)

        video_title = self._html_search_regex(
            r'<title>(?P<title>.+?) - xHamster\.com</title>', webpage, 'title')

        # Only a few videos have an description
        mobj = re.search(r'<span>Description: </span>([^<]+)', webpage)
        video_description = mobj.group(1) if mobj else None

        mobj = re.search(r'hint=\'(?P<upload_date_Y>[0-9]{4})-(?P<upload_date_m>[0-9]{2})-(?P<upload_date_d>[0-9]{2}) [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{3,4}\'', webpage)
        if mobj:
            video_upload_date = mobj.group('upload_date_Y')+mobj.group('upload_date_m')+mobj.group('upload_date_d')
        else:
            video_upload_date = None
            self._downloader.report_warning('Unable to extract upload date')

        video_uploader_id = self._html_search_regex(
            r'<a href=\'/user/[^>]+>(?P<uploader_id>[^<]+)',
            webpage, 'uploader id', default='anonymous')

        video_thumbnail = self._search_regex(
            r'\'image\':\'(?P<thumbnail>[^\']+)\'',
            webpage, 'thumbnail', fatal=False)

        age_limit = self._rta_search(webpage)

        hd = is_hd(webpage)
        video_url = extract_video_url(webpage)
        formats = [{
            'url': video_url,
            'format_id': 'hd' if hd else 'sd',
            'preference': 0,
        }]

        video_mp4_url = extract_mp4_video_url(webpage)
        if video_mp4_url is not None:
            formats.append({
                'url': video_mp4_url,
                'ext': 'mp4',
                'format_id': 'mp4-hd' if hd else 'mp4-sd',
                'preference': 1,
            })

        if not hd:
            webpage = self._download_webpage(
                mrss_url + '?hd', video_id, note='Downloading HD webpage')
            if is_hd(webpage):
                video_url = extract_video_url(webpage)
                formats.append({
                    'url': video_url,
                    'format_id': 'hd',
                    'preference': 2,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'description': video_description,
            'upload_date': video_upload_date,
            'uploader_id': video_uploader_id,
            'thumbnail': video_thumbnail,
            'age_limit': age_limit,
        }
