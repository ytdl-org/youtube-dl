# -*- encoding: utf-8 -*-
from .common import InfoExtractor, ExtractorError


class TvpIE(InfoExtractor):
    IE_NAME = 'tvp.pl'
    _VALID_URL = r'https?://(\w+\.)+tvp\.pl/(?P<id>\d+)/.*'

    _VIDEO_LISTING_URL = ('http://www.api.v3.tvp.pl/shared/listing.php'
                          '?dump=json&direct=true&count=-1&parent_id={id}')
    _META_URL = 'http://www.tvp.pl/shared/video_data.php?dump=json&video_id={id}'
    _TOKENIZER_URL = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id={id}'
    _FILE_INFO_URL = 'http://www.tvp.pl/pub/stat/videofileinfo?video_id={id}'
    _IGNORED_MIMETYPES = 'application/vnd.ms-ss', 'application/x-mpegurl'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/4278035/odc-2',
        'md5': 'cdd98303338b8a7f7abab5cd14092bf2',
        'info_dict': {
            'id': '4278035',
            'ext': 'wmv',
            'title': 'Ogniem i mieczem, odc. 2',
            'description': 'Bohun dowiaduje się o złamaniu przez kniahinię danego mu słowa i wyrusza do Rozłogów. Helenie w ostatniej chwili udaje się uciec dzięki pomocy Zagłoby.'
        },
        }, {
        'url': 'http://warszawa.tvp.pl/23433721/03012016',
        'md5': '8740c6e0532f37e836104f3fb38921d9',
        'info_dict': {
            'id': '23433721',
            'ext': 'mp4',
            'title': 'Echa tygodnia – kraj, 03.01.2016',
        },
    }, {
        'url': 'http://www.rodzinka.tvp.pl/22729075/odc-169',
        'md5': '4dc102e0883555d31b120e8328c02022',
        'info_dict': {
            'id': '22353810',
            'ext': 'mp4',
            'title': 'rodzinka.pl, odc. 169',
            'description': 'Natalia szykuje dla Marii paczkę z ubrankami dla dziecka,\nale ciężko jej się z nimi rozstać – wiążę się z tym zbyt wiele wspomnień. Kacper chce wymusić od Ludwika pieniądze opowiadając o wróżce zębuszcze. A czy zna tak zwanego „Skrzata Dlatata”?',
            },
    }, {
        'url': 'http://vod.tvp.pl/194536/i-seria-odc-13',
        'md5': '8aa518c15e5cc32dfe8db400dc921fbb',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, I seria – odc. 13',
            'description': 'Czesław prosi Marię o dostarczenie Władkowi zarazki tyfusu. Jeśli zachoruje zostanie przewieziony do szpitala skąd łatwiej będzie go odbić. Czy matka zdecyduje się zarazić syna?'
        },
    }, {
        'url': 'http://vod.tvp.pl/17834272/odc-39',
        'md5': 'dafdadb130a45e79bab64aed94b73661',
        'info_dict': {
            'id': '17834272',
            'ext': 'mp4',
            'title': 'Na sygnale, odc. 39',
            'description': 'Ekipa Wiktora ratuje młodą matkę, która spadła ze schodów trzymając na rękach noworodka. Okazuje się, że dziewczyna jest surogatką, a biologiczni rodzice dziecka próbują zmusić ją do oddania synka…',
        },
    }, {
        'url': 'http://vod.tvp.pl/4278026/ogniem-i-mieczem',
        'info_dict': {
            'title': 'Ogniem i mieczem',
            'id': '4278026',
            'description': 'Romans z historią w tle',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://vod.tvp.pl/9329207/',
        'info_dict': {
            'title': 'Boso przez świat',
            'id': '9329207',
            'description': 'Docieramy do plemion w zapomnianych regionach naszej planety. Poznajemy ich kulturę, wierzenia i zwyczaje. Na ile są podobne do naszych? Wojciech Cejrowski jest naszym przewodnikiem po najbardziej dzikich zakątkach globu.',
        },
        'playlist_count': 86,
    }]

    def _get_json(self, url, entry_id):
        formatted_url = url.format(id=int(entry_id))
        return self._download_json(formatted_url, entry_id)

    def _format_formats(self, formats, video_id):

        mime_ext = {
            'video/x-ms-wmv': 'wmv',
            'video/mp4': 'mp4'
        }

        viable_formats = []
        for f in formats:
            if f['mimeType'] in self._IGNORED_MIMETYPES:
                continue

            elif f['mimeType'].startswith('video/'):
                viable_formats.append(
                    {'url': f['url'],
                     'ext': mime_ext.get(f['mimeType']),
                     'vbr': f['totalBitrate']})

        return viable_formats

    @staticmethod
    def _guess_title(item):
        title_root = item.get('title_root')
        title = item.get('title')
        website_title = item.get('website_title')
        if title_root:
            return item['title_root']
        if title and website_title:
            return '{}, {}'.format(website_title, title)
        return title

    def _get_video(self, context):
        video_id = str(context['material_id'])
        title = self._guess_title(context)
        url = context['url']
        description = context.get('description_root')

        formats_req = self._get_json(self._TOKENIZER_URL, video_id)
        req_status = formats_req['status']
        if req_status == 'NOT_PLAYABLE':
            raise ExtractorError('(%s) is not playable' % title,
                                 expected=True, video_id=video_id)
        elif req_status != 'OK':
            raise ExtractorError('(%s) unknown status: %s' % (title, req_status),
                                 video_id=video_id)
        formats = self._format_formats(formats_req['formats'], video_id)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'formats': formats,
        }

    def _get_playlist_videos(self, playlist_id):
        ids = [playlist_id]

        while ids:
            item_id = ids.pop()
            listing = self._get_json(self._VIDEO_LISTING_URL, item_id)
            for item in listing['items']:
                if 'directory_video' in item['types']:
                    ids.append(item['_id'])
                if 'video' in item['types'] and item['is_released']:
                    yield {
                        '_type': 'url',
                        'title': self._guess_title(item),
                        'url': item['url']}

    def _get_playlist(self, context):
        pls_id = str(context['material_id'])
        title = self._guess_title(context)
        description = context.get('lead_root')

        return self.playlist_result(self._get_playlist_videos(pls_id),
                                    pls_id, title, description)

    def _real_extract(self, url):
        entry_id = self._match_id(url)
        ctx = self._get_json(self._META_URL, entry_id)['context']
        if ctx['format_id'] == 0:
            file_info = self._get_json(self._FILE_INFO_URL, entry_id)
            original_id = file_info.get('copy_of_object_id')
            if original_id:
                ctx = self._get_json(self._META_URL, original_id)['context']

        is_playlist = ctx['format_id'] == 0
        return self._get_playlist(ctx) if is_playlist else self._get_video(ctx)


class TvpLegacyIE(TvpIE):
    IE_NAME = 'tvp.pl'
    _VALID_URL = r'https?://(?:vod|www)\.tvp\.pl/.*/(?P<id>\d+)$'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/filmy-fabularne/filmy-za-darmo/ogniem-i-mieczem/wideo/odc-2/4278035',
        'md5': 'cdd98303338b8a7f7abab5cd14092bf2',
        'info_dict': {
            'id': '4278035',
            'ext': 'wmv',
            'title': 'Ogniem i mieczem, odc. 2',
            'description': 'Bohun dowiaduje się o złamaniu przez kniahinię danego mu słowa i wyrusza do Rozłogów. Helenie w ostatniej chwili udaje się uciec dzięki pomocy Zagłoby.',
        },
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/czas-honoru/sezon-1-1-13/i-seria-odc-13/194536',
        'md5': '8aa518c15e5cc32dfe8db400dc921fbb',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, I seria – odc. 13',
            'description': 'Czesław prosi Marię o dostarczenie Władkowi zarazki tyfusu. Jeśli zachoruje zostanie przewieziony do szpitala skąd łatwiej będzie go odbić. Czy matka zdecyduje się zarazić syna?',
        },
    }, {
        'url': 'http://www.tvp.pl/there-can-be-anything-so-i-shortened-it/17916176',
        'md5': 'b0005b542e5b4de643a9690326ab1257',
        'info_dict': {
            'id': '17916176',
            'ext': 'mp4',
            'title': 'TVP Gorzów pokaże filmy studentów z podroży dookoła świata',
        },
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/na-sygnale/sezon-2-27-/odc-39/17834272',
        'md5': 'dafdadb130a45e79bab64aed94b73661',
        'info_dict': {
            'id': '17834272',
            'ext': 'mp4',
            'title': 'Na sygnale, odc. 39',
            'description': 'Ekipa Wiktora ratuje młodą matkę, która spadła ze schodów trzymając na rękach noworodka. Okazuje się, że dziewczyna jest surogatką, a biologiczni rodzice dziecka próbują zmusić ją do oddania synka…',
        },
    }]
