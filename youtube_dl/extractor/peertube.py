# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_resolution,
    try_get,
    unified_timestamp,
    urljoin,
)


class PeerTubeIE(InfoExtractor):
    _INSTANCES_RE = r'''(?:
                            # Taken from https://instances.joinpeertube.org/instances
                            tube\.openalgeria\.org|
                            peertube\.pointsecu\.fr|
                            peertube\.nogafa\.org|
                            peertube\.pl|
                            megatube\.lilomoino\.fr|
                            peertube\.tamanoir\.foucry\.net|
                            peertube\.inapurna\.org|
                            peertube\.netzspielplatz\.de|
                            video\.deadsuperhero\.com|
                            peertube\.devosi\.org|
                            peertube\.1312\.media|
                            tube\.worldofhauru\.xyz|
                            tube\.bootlicker\.party|
                            skeptikon\.fr|
                            peertube\.geekshell\.fr|
                            tube\.opportunis\.me|
                            peertube\.peshane\.net|
                            video\.blueline\.mg|
                            tube\.homecomputing\.fr|
                            videos\.cloudfrancois\.fr|
                            peertube\.viviers-fibre\.net|
                            tube\.ouahpiti\.info|
                            video\.tedomum\.net|
                            video\.g3l\.org|
                            fontube\.fr|
                            peertube\.gaialabs\.ch|
                            peertube\.extremely\.online|
                            peertube\.public-infrastructure\.eu|
                            tube\.kher\.nl|
                            peertube\.qtg\.fr|
                            tube\.22decembre\.eu|
                            facegirl\.me|
                            video\.migennes\.net|
                            janny\.moe|
                            tube\.p2p\.legal|
                            video\.atlanti\.se|
                            troll\.tv|
                            peertube\.geekael\.fr|
                            vid\.leotindall\.com|
                            video\.anormallostpod\.ovh|
                            p-tube\.h3z\.jp|
                            tube\.darfweb\.eu|
                            videos\.iut-orsay\.fr|
                            peertube\.solidev\.net|
                            videos\.symphonie-of-code\.fr|
                            testtube\.ortg\.de|
                            videos\.cemea\.org|
                            peertube\.gwendalavir\.eu|
                            video\.passageenseine\.fr|
                            videos\.festivalparminous\.org|
                            peertube\.touhoppai\.moe|
                            peertube\.duckdns\.org|
                            sikke\.fi|
                            peertube\.mastodon\.host|
                            firedragonvideos\.com|
                            vidz\.dou\.bet|
                            peertube\.koehn\.com|
                            peer\.hostux\.social|
                            share\.tube|
                            peertube\.walkingmountains\.fr|
                            medias\.libox\.fr|
                            peertube\.moe|
                            peertube\.xyz|
                            jp\.peertube\.network|
                            videos\.benpro\.fr|
                            tube\.otter\.sh|
                            peertube\.angristan\.xyz|
                            peertube\.parleur\.net|
                            peer\.ecutsa\.fr|
                            peertube\.heraut\.eu|
                            peertube\.tifox\.fr|
                            peertube\.maly\.io|
                            vod\.mochi\.academy|
                            exode\.me|
                            coste\.video|
                            tube\.aquilenet\.fr|
                            peertube\.gegeweb\.eu|
                            framatube\.org|
                            thinkerview\.video|
                            tube\.conferences-gesticulees\.net|
                            peertube\.datagueule\.tv|
                            video\.lqdn\.fr|
                            meilleurtube\.delire\.party|
                            tube\.mochi\.academy|
                            peertube\.dav\.li|
                            media\.zat\.im|
                            pytu\.be|
                            peertube\.valvin\.fr|
                            peertube\.nsa\.ovh|
                            video\.colibris-outilslibres\.org|
                            video\.hispagatos\.org|
                            tube\.svnet\.fr|
                            peertube\.video|
                            videos\.lecygnenoir\.info|
                            peertube3\.cpy\.re|
                            peertube2\.cpy\.re|
                            videos\.tcit\.fr|
                            peertube\.cpy\.re
                        )'''
    _VALID_URL = r'''(?x)
                    https?://
                        %s
                        /(?:videos/(?:watch|embed)|api/v\d/videos)/
                        (?P<id>[^/?\#&]+)
                    ''' % _INSTANCES_RE
    _TESTS = [{
        'url': 'https://peertube.moe/videos/watch/2790feb0-8120-4e63-9af3-c943c69f5e6c',
        'md5': '80f24ff364cc9d333529506a263e7feb',
        'info_dict': {
            'id': '2790feb0-8120-4e63-9af3-c943c69f5e6c',
            'ext': 'mp4',
            'title': 'wow',
            'description': 'wow such video, so gif',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'timestamp': 1519297480,
            'upload_date': '20180222',
            'uploader': 'Luclu7',
            'uploader_id': '7fc42640-efdb-4505-a45d-a15b1a5496f1',
            'uploder_url': 'https://peertube.nsa.ovh/accounts/luclu7',
            'license': 'Unknown',
            'duration': 3,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': list,
            'categories': list,
        }
    }, {
        'url': 'https://peertube.tamanoir.foucry.net/videos/watch/0b04f13d-1e18-4f1d-814e-4979aa7c9c44',
        'only_matching': True,
    }, {
        # nsfw
        'url': 'https://tube.22decembre.eu/videos/watch/9bb88cd3-9959-46d9-9ab9-33d2bb704c39',
        'only_matching': True,
    }, {
        'url': 'https://tube.22decembre.eu/videos/embed/fed67262-6edb-4d1c-833b-daa9085c71d7',
        'only_matching': True,
    }, {
        'url': 'https://tube.openalgeria.org/api/v1/videos/c1875674-97d0-4c94-a058-3f7e64c962e8',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [
            mobj.group('url')
            for mobj in re.finditer(
                r'''(?x)<iframe[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//%s/videos/embed/[^/?\#&]+)\1'''
                % PeerTubeIE._INSTANCES_RE, webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            urljoin(url, '/api/v1/videos/%s' % video_id), video_id)

        title = video['name']

        formats = []
        for file_ in video['files']:
            if not isinstance(file_, dict):
                continue
            file_url = file_.get('fileUrl')
            if not file_url or not isinstance(file_url, compat_str):
                continue
            file_size = int_or_none(file_.get('size'))
            format_id = try_get(
                file_, lambda x: x['resolution']['label'], compat_str)
            f = parse_resolution(format_id)
            f.update({
                'url': file_url,
                'format_id': format_id,
                'filesize': file_size,
            })
            formats.append(f)
        self._sort_formats(formats)

        def account_data(field):
            return try_get(video, lambda x: x['account'][field], compat_str)

        category = try_get(video, lambda x: x['category']['label'], compat_str)
        categories = [category] if category else None

        nsfw = video.get('nsfw')
        if nsfw is bool:
            age_limit = 18 if nsfw else 0
        else:
            age_limit = None

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': urljoin(url, video.get('thumbnailPath')),
            'timestamp': unified_timestamp(video.get('publishedAt')),
            'uploader': account_data('displayName'),
            'uploader_id': account_data('uuid'),
            'uploder_url': account_data('url'),
            'license': try_get(
                video, lambda x: x['licence']['label'], compat_str),
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('views')),
            'like_count': int_or_none(video.get('likes')),
            'dislike_count': int_or_none(video.get('dislikes')),
            'age_limit': age_limit,
            'tags': try_get(video, lambda x: x['tags'], list),
            'categories': categories,
            'formats': formats,
        }
