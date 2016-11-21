from __future__ import unicode_literals

from .nuevo import NuevoBaseIE
from ..utils import int_or_none


class RulePornIE(NuevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ruleporn\.com/(?:[^/?#&]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://ruleporn.com/brunette-nympho-chick-takes-her-boyfriend-in-every-angle/',
        'md5': '86861ebc624a1097c7c10eaf06d7d505',
        'info_dict': {
            'id': '48212',
            'display_id': 'brunette-nympho-chick-takes-her-boyfriend-in-every-angle',
            'ext': 'mp4',
            'title': 'Brunette Nympho Chick Takes Her Boyfriend In Every Angle',
            'description': 'md5:6d28be231b981fff1981deaaa03a04d5',
            'age_limit': 18,
            'duration': 635.1,
        },
    }, {
        'url': 'http://ruleporn.com/short-sweet-amateur-milf-sex-action/',
        'md5': '9ec215fe7ecc19323eba42d0f16af054',
        'info_dict': {
            'id': '777084',
            'display_id': 'short-sweet-amateur-milf-sex-action',
            'ext': 'mp4',
            'title': 'Short but sweet amateur MILF sex action',
            'description': 'md5:a20fabf0f267839dfcde0b56a418147f',
            'age_limit': 18,
            'duration': 182,
        },
    }, {
        'url': 'http://ruleporn.com/horny-bruentte-teen-getting-penetrated-in-a-doggy/',
        'md5': '6f3eebefd27d1b9d28f1366d951aec56',
        'info_dict': {
            'id': '975925',
            'display_id': 'horny-bruentte-teen-getting-penetrated-in-a-doggy',
            'ext': 'mp4',
            'title': 'Horny Brunette Teen Getting Penetrated In A Doggy',
            'description': 'md5:2c22da523c47418e254343f9ca454758',
            'age_limit': 18,
            'duration': 112,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        title = self._search_regex(
            r'<h2[^>]+title=(["\'])\s?(?P<url>.+?)\1',
            webpage, 'title', group='url')
        description = self._html_search_meta('description', webpage)

        video_url = self._search_regex(
            r'<div\s+id=\"player\">\s+<iframe[\w\W]+?(?:src=[\"\']?(?P<url>[^\"\' ]+))', webpage, 'video url')

        video_id = self._search_regex(
            r'lovehomeporn\.com/embed/(\d+)', video_url, 'video_id', default=None)

        if video_id:
            info = self._extract_nuevo(
                'http://lovehomeporn.com/media/nuevo/econfig.php?key=%s&rp=true' % video_id,
                video_id)

            info.update({
                'display_id': display_id,
                'title': title,
                'description': description,
                'age_limit': 18
            })

        else:
            video_page = self._download_webpage(video_url, display_id)

            js_str = self._search_regex(
                r'var\s+item\s+=\s+({.+(?=};)});', video_page, 'js_str')

            js_obj = self._parse_json(js_str, display_id)

            video_id = '%s' % js_obj.get('id')
            duration = int_or_none(js_obj.get('video_duration'))
            thumbnail = js_obj.get('url_thumb')

            formats = []
            for element_name, format_id in (('url_mp4_lowres', 'ld'), ('url_mp4', 'sd'), ('url_orig', 'hd')):
                video_url = js_obj.get(element_name)
                formats.append({
                    'url': video_url,
                    'format_id': format_id
                })
            self._check_formats(formats, video_id)

            info = {
                'id': video_id,
                'display_id': display_id,
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'duration': duration,
                'age_limit': 18,
                'formats': formats
            }

        return info
