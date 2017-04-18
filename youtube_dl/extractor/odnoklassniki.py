# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_etree_fromstring,
    compat_parse_qs,
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    unified_strdate,
    int_or_none,
    qualities,
    unescapeHTML,
)


class OdnoklassnikiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|m|mobile)\.)?(?:odnoklassniki|ok)\.ru/(?:video(?:embed)?|web-api/video/moviePlayer)/(?P<id>[\d-]+)'
    _TESTS = [{
        # metadata in JSON
        'url': 'http://ok.ru/video/20079905452',
        'md5': '6ba728d85d60aa2e6dd37c9e70fdc6bc',
        'info_dict': {
            'id': '20079905452',
            'ext': 'mp4',
            'title': 'Культура меняет нас (прекрасный ролик!))',
            'duration': 100,
            'upload_date': '20141207',
            'uploader_id': '330537914540',
            'uploader': 'Виталий Добровольский',
            'like_count': int,
            'age_limit': 0,
        },
        'skip': 'Video has been blocked',
    }, {
        # metadataUrl
        'url': 'http://ok.ru/video/63567059965189-0?fromTime=5',
        'md5': '6ff470ea2dd51d5d18c295a355b0b6bc',
        'info_dict': {
            'id': '63567059965189-0',
            'ext': 'mp4',
            'title': 'Девушка без комплексов ...',
            'duration': 191,
            'upload_date': '20150518',
            'uploader_id': '534380003155',
            'uploader': '☭ Андрей Мещанинов ☭',
            'like_count': int,
            'age_limit': 0,
            'start_time': 5,
        },
    }, {
        # YouTube embed (metadataUrl, provider == USER_YOUTUBE)
        'url': 'http://ok.ru/video/64211978996595-1',
        'md5': '2f206894ffb5dbfcce2c5a14b909eea5',
        'info_dict': {
            'id': '64211978996595-1',
            'ext': 'mp4',
            'title': 'Космическая среда от 26 августа 2015',
            'description': 'md5:848eb8b85e5e3471a3a803dae1343ed0',
            'duration': 440,
            'upload_date': '20150826',
            'uploader_id': 'tvroscosmos',
            'uploader': 'Телестудия Роскосмоса',
            'age_limit': 0,
        },
    }, {
        # YouTube embed (metadata, provider == USER_YOUTUBE, no metadata.movie.title field)
        'url': 'http://ok.ru/video/62036049272859-0',
        'info_dict': {
            'id': '62036049272859-0',
            'ext': 'mp4',
            'title': 'МУЗЫКА     ДОЖДЯ .',
            'description': 'md5:6f1867132bd96e33bf53eda1091e8ed0',
            'upload_date': '20120106',
            'uploader_id': '473534735899',
            'uploader': 'МARINA D',
            'age_limit': 0,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Video has not been found',
    }, {
        'url': 'http://ok.ru/web-api/video/moviePlayer/20079905452',
        'only_matching': True,
    }, {
        'url': 'http://www.ok.ru/video/20648036891',
        'only_matching': True,
    }, {
        'url': 'http://www.ok.ru/videoembed/20648036891',
        'only_matching': True,
    }, {
        'url': 'http://m.ok.ru/video/20079905452',
        'only_matching': True,
    }, {
        'url': 'http://mobile.ok.ru/video/20079905452',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        start_time = int_or_none(compat_parse_qs(
            compat_urllib_parse_urlparse(url).query).get('fromTime', [None])[0])

        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://ok.ru/video/%s' % video_id, video_id)

        error = self._search_regex(
            r'[^>]+class="vp_video_stub_txt"[^>]*>([^<]+)<',
            webpage, 'error', default=None)
        if error:
            raise ExtractorError(error, expected=True)

        player = self._parse_json(
            unescapeHTML(self._search_regex(
                r'data-options=(?P<quote>["\'])(?P<player>{.+?%s.+?})(?P=quote)' % video_id,
                webpage, 'player', group='player')),
            video_id)

        flashvars = player['flashvars']

        metadata = flashvars.get('metadata')
        if metadata:
            metadata = self._parse_json(metadata, video_id)
        else:
            metadata = self._download_json(
                compat_urllib_parse_unquote(flashvars['metadataUrl']),
                video_id, 'Downloading metadata JSON')

        movie = metadata['movie']

        # Some embedded videos may not contain title in movie dict (e.g.
        # http://ok.ru/video/62036049272859-0) thus we allow missing title
        # here and it's going to be extracted later by an extractor that
        # will process the actual embed.
        provider = metadata.get('provider')
        title = movie['title'] if provider == 'UPLOADED_ODKL' else movie.get('title')

        thumbnail = movie.get('poster')
        duration = int_or_none(movie.get('duration'))

        author = metadata.get('author', {})
        uploader_id = author.get('id')
        uploader = author.get('name')

        upload_date = unified_strdate(self._html_search_meta(
            'ya:ovs:upload_date', webpage, 'upload date', default=None))

        age_limit = None
        adult = self._html_search_meta(
            'ya:ovs:adult', webpage, 'age limit', default=None)
        if adult:
            age_limit = 18 if adult == 'true' else 0

        like_count = int_or_none(metadata.get('likeCount'))

        info = {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'upload_date': upload_date,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'like_count': like_count,
            'age_limit': age_limit,
            'start_time': start_time,
        }

        if provider == 'USER_YOUTUBE':
            info.update({
                '_type': 'url_transparent',
                'url': movie['contentId'],
            })
            return info

        quality = qualities(('4', '0', '1', '2', '3', '5'))

        formats = [{
            'url': f['url'],
            'ext': 'mp4',
            'format_id': f['name'],
        } for f in metadata['videos']]

        m3u8_url = metadata.get('hlsManifestUrl')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        dash_manifest = metadata.get('metadataEmbedded')
        if dash_manifest:
            formats.extend(self._parse_mpd_formats(
                compat_etree_fromstring(dash_manifest), 'mpd'))

        for fmt in formats:
            fmt_type = self._search_regex(
                r'\btype[/=](\d)', fmt['url'],
                'format type', default=None)
            if fmt_type:
                fmt['quality'] = quality(fmt_type)

        self._sort_formats(formats)

        info['formats'] = formats
        return info
