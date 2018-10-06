# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import month_by_name


class FranceInterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?franceinter\.fr/emissions/(?P<id>[^?#]+)'

    _TESTS = [
        {
            'url': 'https://www.franceinter.fr/emissions/affaires-sensibles/affaires-sensibles-07-septembre-2016',
            'md5': '9e54d7bdb6fdc02a841007f8a975c094',
            'info_dict': {
                'id': 'affaires-sensibles/affaires-sensibles-07-septembre-2016',
                'ext': 'mp3',
                'title': 'Affaire Cahuzac : le contentieux du compte en Suisse',
                'description': 'md5:401969c5d318c061f86bda1fa359292b',
                'upload_date': '20160907',
            },
        },
        {
            'note': 'Audio + video (Dailymotion embed)',
            'url': 'https://www.franceinter.fr/emissions/l-instant-m/l-instant-m-13-fevrier-2018',
            'info_dict': {
                'id': 'x6eow0v',
                'ext': 'mp4',
                'title': 'Propagande, stéréotypes, spectaculaire : les jeux vidéo font-ils du mal à l\'Histoire ?',
                'description': 'Le youtubeur Nota Bene pour \"History’s Creed\", la nouvelle websérie d\'ARTE Creative qui explore la relation Jeux vidéo et Histoire. Que nos enfants peuvent-ils apprendre de la Révolution française en jouant à « Assasin’s Creed » ? Et quelle vision auront-il de la Seconde Guerre mondiale en plongeant dans « Call of duty » ?   Les jeux vidéo constituent un support majeur de représentation de l’Histoire avec un grand H. Simple décor ? Prétexte narratif ? Ou nouvelle lecture du passé ?  Le jeu vidéo est devenu un médium si puissant et si mondialisé qu’il nous faut non seulement interroger la crédibilité de ses représentations, mais aussi l’idéologie de ses récits. Mon invité n’ignore rien des stéréotypes historiques, du spectaculaire trompeur et des tentations propagandistes auxquelles peuvent céder les jeux vidéo. Ils n’en demeurent pas moins, à ses yeux, un pont formidable vers la connaissance.      Ben dit Nota Bene, sur Youtube, sa chaîne d’histoire y est massivement suivie. Il y raconte l’Histoire de manière ludique et pointue à la fois. Sans hésiter à piocher dans la pop culture, type Harry Potter ou Game of Thrones…    History’s Creed, c’est à voir sur le site d’Arte, arte creative, c’est en 10 petits épisodes. Et c’est formidable.  L\'Instant M  , l’invité était Nota Bene (9h40 - 13 Février 2018) Retrouvez L\'Instant M sur www.franceinter.fr',
                'uploader_id': 'x2q2ez',
                'timestamp': 1518516881,
                'uploader': 'France Inter',
                'upload_date': '20180213',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # If there is a video version, use that instead
        maybe_video_uuid = re.search(r'data-video-anchor-target=["\']([^"\']+)', webpage)
        if maybe_video_uuid:
            video_uuid = maybe_video_uuid.group(1)
            video_url = self._search_regex(
                r'(?sx)data-uuid=["\']%s.*?<iframe[^>]*src=["\']([^"\']+)' % video_uuid,
                webpage, 'video url', fatal=False, group=1)

            if video_url:
                return self.url_result(video_url)

        audio_url = self._search_regex(
            r'(?s)<div[^>]+class=["\']page-diffusion["\'][^>]*>.*?<button[^>]+data-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'audio url', group='url')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        upload_date_str = self._search_regex(
            r'class=["\']\s*cover-emission-period\s*["\'][^>]*>[^<]+\s+(\d{1,2}\s+[^\s]+\s+\d{4})<',
            webpage, 'upload date', fatal=False)
        if upload_date_str:
            upload_date_list = upload_date_str.split()
            upload_date_list.reverse()
            upload_date_list[1] = '%02d' % (month_by_name(upload_date_list[1], lang='fr') or 0)
            upload_date_list[2] = '%02d' % int(upload_date_list[2])
            upload_date = ''.join(upload_date_list)
        else:
            upload_date = None

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'formats': [{
                'url': audio_url,
                'vcodec': 'none',
            }],
        }
