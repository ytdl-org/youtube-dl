# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import month_by_name


class FranceInterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceinter\.fr/emissions/(?P<id>[^?#]+)'

    _TEST = {
        'url': 'https://www.franceinter.fr/emissions/la-tete-au-carre/la-tete-au-carre-14-septembre-2016',
        'md5': '4e3aeb58fe0e83d7b0581fa213c409d0',
        'info_dict': {
            'id': 'la-tete-au-carre/la-tete-au-carre-14-septembre-2016',
            'ext': 'mp3',
            'title': 'Et si les rêves pouvaient nous aider à agir dans notre vie quotidienne ?',
            'description': 'md5:a245dd62cf5bf51de915f8d9956d180a',
            'upload_date': '20160914',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'(?s)<div[^>]+class=["\']page-diffusion["\'][^>]*>.*?<button[^>]+data-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'video url', group='url')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        upload_date_str = self._search_regex(
            r'class=["\']cover-emission-period["\'][^>]*>[^<]+\s+(\d{1,2}\s+[^\s]+\s+\d{4})<',
            webpage, 'upload date', fatal=False)
        if upload_date_str:
            upload_date_list = upload_date_str.split()
            upload_date_list.reverse()
            upload_date_list[1] = '%02d' % (month_by_name(upload_date_list[1], lang='fr') or 0)
            upload_date = ''.join(upload_date_list)
        else:
            upload_date = None

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'formats': [{
                'url': video_url,
                'vcodec': 'none',
            }],
        }
