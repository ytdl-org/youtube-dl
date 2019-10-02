# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json, RegexNotFoundError, urljoin, get_element_by_id, unified_strdate
)

import json
import re


class HHUIE(InfoExtractor):
    _VALID_URL = r'https://mediathek\.hhu\.de/watch/(?P<id>.+)'
    _TEST = {
        'url': 'https://mediathek.hhu.de/watch/2dd05982-ea45-4108-9620-0c36e6ed8df5',
        'md5': 'b99ff77f2148b1e754555abdf53f0e51',
        'info_dict': {
            'id': '2dd05982-ea45-4108-9620-0c36e6ed8df5',
            'ext': 'mp4',
            'title': 'Das Multimediazentrum',
            'description': '',
            'categories': ['Imagefilme'],
            'tags': [
                'MMZ', 'Multimediazentrum', 'Heinrich-Heine-Universität',
                'UKD', 'eLearning', 'Abstimmsysteme', 'Portale',
                'Studierendenportal', 'Lehrfilme', 'Lehrfilm',
                'Operationsfilme', 'Vorlesungsaufzeichnung', 'Multimedia',
                'ZIM', 'HHU', 'Ute', 'Clames',  # yes, that's incorrect
            ],
            'uploader': 'clames',
            'uploader_id': 'clames',
            'license': 'CC BY 3.0 DE',
            'upload_date': '20150126',
            'thumbnail': 'https://mediathek.hhu.de/thumbs/2dd05982-ea45-4108-9620-0c36e6ed8df5/thumb_000.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, webpage_url = self._download_webpage_handle(url, video_id)
        if webpage_url.geturl().startswith("https://sts."):
            self.raise_login_required()
            # Some videos need a login, maybe TODO.
        try:
            config_js = self._search_regex(
                r'playerInstance\.setup\(([^;]+)\);', webpage, 'config_js'
            )
            # remove 'link: encodeURI("<our url>"),'
            if 'link: encodeURI' in config_js:
                encode_begin = config_js.find('link: encodeURI')
                encode_end = config_js.find(')', encode_begin)
                config_js = (
                    config_js[:encode_begin] + config_js[encode_end + 2:]
                )
                del encode_begin, encode_end
            config = json.loads(js_to_json(config_js))
            if len(config['playlist']) > 1:
                self.report_warning(
                    'more than one video, just taking the first one'
                )
            video = config['playlist'][0]
            formats = [
                {
                    'url': urljoin('https://mediathek.hhu.de/', source['file']),
                    'format_note': source.get('label'),
                    'format_id': source['file'].split("/")[-1],
                }
                for source in video['sources']
            ]
            formats.reverse()  # config sorts from highest to lowest quality
            title = video.get('title')
            thumbnail = video.get('image')
            thumbnail = urljoin('https://mediathek.hhu.de/', thumbnail) if thumbnail else None

        except (RegexNotFoundError, ValueError):
            self.report_warning('failed to get player config, guessing formats')
            # This will likely work but better warn.
            file_id = self._html_search_regex(
                r"{ file: '\/movies\/(.+?)\/v_100\.mp4', label: '",
                webpage, 'file_id'
            )
            formats = [
                ({'url': format_url.format(file_id)})
                for format_url in (
                    'https://mediathek.hhu.de/movies/{}/v_10.webm',
                    'https://mediathek.hhu.de/movies/{}/v_10.mp4',
                    'https://mediathek.hhu.de/movies/{}/v_50.webm',
                    'https://mediathek.hhu.de/movies/{}/v_50.mp4',
                    'https://mediathek.hhu.de/movies/{}/v_100.webm',
                    'https://mediathek.hhu.de/movies/{}/v_100.mp4',
                )
            ]
            title = thumbnail = None
        if not title:
            title = self._html_search_regex(
                r'<h1 id="mt_watch-headline-title">\s+(.+?)\s+<\/h1>',
                webpage, 'title'
            )
        if not title:
            title = self._og_search_title(webpage, fatal=False)
        description = self._html_search_regex(
            r'<p id="mt_watch-description" class="watch-description">\s+(.+?)\s+<\/p>',
            webpage, 'description', fatal=False
        )
        if not description:
            description = self._og_search_description(webpage, default='')
        if not thumbnail:
            thumbnail = self._og_search_property(
                'image:secure_url', webpage, 'thumbnail', fatal=False
            )
        uploader = self._html_search_regex(
            r'<a id="mt_content_placeholder_videoinfo_createdby" class="author" href=".+">(.+?)<\/a>',
            webpage, 'uploader', fatal=False
        )
        uploader_id = self._html_search_regex(
            r'<a id="mt_content_placeholder_videoinfo_createdby" class="author" href="/user/(.+)">.+?<\/a>',
            webpage, 'uploader_id', fatal=False
        )
        # CC licenses get a image with an appropriate alt text
        license_img = get_element_by_id('mt_watch_license', webpage)
        if license_img:
            license = self._search_regex(
                r'alt="(.+)"', license_img, 'license_img', fatal=False
            )
        if not license_img or not license:
            # other licenses are just text
            license = self._html_search_regex(
                r'<div id="mt_content_placeholder_videotabs_mt_videotabs_formview_video_license" class="video-license">(.+)<\/div>',
                webpage, 'license_text', fatal=False
            )
        upload_date = _date(self._html_search_regex(
            r'<span class="watch-information-date added">(.+?)<\/span>',
            webpage, 'upload_date', fatal=False
        ))
        category = self._html_search_regex(
            r'<a href="/category/.+">(.+)</a>', webpage, 'category', fatal=False
        )
        tags_html = get_element_by_id('mt_watch_info_tag_list', webpage)
        tags = _tags(tags_html)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'license': license,
            'categories': [category],  # there's just one category per video
            'tags': tags,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'formats': formats,
        }


def _date(str_containing_date):
    """Parse the string 'at (M)M/(D)D/YYYY' to YYYYMMDD."""
    return unified_strdate(str_containing_date.split(' ')[1], day_first=False)


def _tags(tags_html):
    """Parse the HTML markup containing the tags."""
    matches = re.findall(r'<a.+>(.+)<\/a>', tags_html)
    return [match.rstrip(',') for match in matches]
