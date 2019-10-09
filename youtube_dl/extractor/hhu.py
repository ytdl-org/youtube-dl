# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json, RegexNotFoundError, get_element_by_id, unified_strdate
)

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
                'ZIM', 'HHU', 'Ute', 'Clames', ],  # yes, that's incorrect
            'uploader': 'clames',
            'uploader_id': 'clames',
            'license': 'CC BY 3.0 DE',
            'upload_date': '20150126',
            'thumbnail': 'https://mediathek.hhu.de/thumbs/2dd05982-ea45-4108-9620-0c36e6ed8df5/thumb_000.jpg', }}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, webpage_url = self._download_webpage_handle(url, video_id)
        if webpage_url.geturl().startswith("https://sts."):
            self.raise_login_required()
            # Some videos need a login, maybe TODO.
        try:
            config_js = self._search_regex(
                r'playerInstance\.setup\(([^;]+)\);', webpage, 'config_js')
            # remove 'link: encodeURI("<our url>"),'
            if 'link: encodeURI' in config_js:
                encode_begin = config_js.find('link: encodeURI')
                encode_end = config_js.find(')', encode_begin)
                config_js = (
                    config_js[:encode_begin] + config_js[encode_end + 2:])
                del encode_begin, encode_end
            config = self._parse_json(
                config_js, video_id, transform_source=js_to_json)
            info = self._parse_jwplayer_data(
                config, video_id, require_title=False,
                base_url='https://mediathek.hhu.de/')
        except (RegexNotFoundError, ValueError):
            self.report_warning('failed to get player config, guessing formats')
            # This will likely work but better warn.
            file_id = self._html_search_regex(
                r"{ file: '\/movies\/(.+?)\/v_100\.mp4', label: '",
                webpage, 'file_id')
            info = {
                'video_id': video_id,
                'formats': [
                    ({'url': format_url.format(file_id)})
                    for format_url in (
                        'https://mediathek.hhu.de/movies/{}/v_10.webm',
                        'https://mediathek.hhu.de/movies/{}/v_10.mp4',
                        'https://mediathek.hhu.de/movies/{}/v_50.webm',
                        'https://mediathek.hhu.de/movies/{}/v_50.mp4',
                        'https://mediathek.hhu.de/movies/{}/v_100.webm',
                        'https://mediathek.hhu.de/movies/{}/v_100.mp4',)]}
        if not info.get('title'):
            info['title'] = self._html_search_regex(
                r'<h1 id="mt_watch-headline-title">\s+(.+?)\s+<\/h1>',
                webpage, 'title')
        if not info.get('title'):
            info['title'] = self._og_search_title(webpage, fatal=False)
        info['description'] = self._html_search_regex(
            r'<p id="mt_watch-description" class="watch-description">\s+(.+?)\s+<\/p>',
            webpage, 'description', fatal=False)
        if not info.get('description'):
            info['description'] = self._og_search_description(webpage, default='')
        if not info.get('thumbnail'):
            info['thumbnail'] = self._og_search_property(
                'image:secure_url', webpage, 'thumbnail', fatal=False)
        info['uploader'] = self._html_search_regex(
            r'<a id="mt_content_placeholder_videoinfo_createdby" class="author" href=".+">(.+?)<\/a>',
            webpage, 'uploader', fatal=False)
        info['uploader_id'] = self._html_search_regex(
            r'<a id="mt_content_placeholder_videoinfo_createdby" class="author" href="/user/(.+)">.+?<\/a>',
            webpage, 'uploader_id', fatal=False)
        # CC licenses get a image with an appropriate alt text
        license_img = get_element_by_id('mt_watch_license', webpage)
        if license_img:
            info['license'] = self._search_regex(
                r'alt="(.+)"', license_img, 'license_img', fatal=False)
        if not license_img or not info.get('license'):
            # other licenses are just text
            info['license'] = self._html_search_regex(
                r'<div id="mt_content_placeholder_videotabs_mt_videotabs_formview_video_license" class="video-license">(.+)<\/div>',
                webpage, 'license_text', fatal=False)
        info['upload_date'] = _date(self._html_search_regex(
            r'<span class="watch-information-date added">(.+?)<\/span>',
            webpage, 'upload_date', fatal=False))
        category = self._html_search_regex(
            r'<a href="/category/.+">(.+)</a>', webpage, 'category', fatal=False)
        info['categories'] = [category]  # there's just one category per video
        tags_html = get_element_by_id('mt_watch_info_tag_list', webpage)
        info['tags'] = _tags(tags_html)
        return info


def _date(str_containing_date):
    """Parse the string 'at (M)M/(D)D/YYYY' to YYYYMMDD."""
    return unified_strdate(str_containing_date.split(' ')[1], day_first=False)


def _tags(tags_html):
    """Parse the HTML markup containing the tags."""
    matches = re.findall(r'<a.+>(.+)<\/a>', tags_html)
    return [match.rstrip(',') for match in matches]
