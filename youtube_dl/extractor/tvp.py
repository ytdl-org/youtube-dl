from .common import InfoExtractor, ExtractorError

VIDEO_LISTING_URL = ('http://www.api.v3.tvp.pl/shared/listing.php'
                     '?dump=json&direct=true&count=-1&parent_id={id}')
META_URL = 'http://www.tvp.pl/shared/video_data.php?dump=json&video_id={id}'
TOKENIZER_URL = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id={id}'
FILE_INFO_URL = 'http://www.tvp.pl/pub/stat/videofileinfo?video_id={id}'
IGNORED_MIMETYPES = 'application/vnd.ms-ss', 'application/x-mpegurl'


class TvpApi:

    def __init__(self, ie):
        """:type ie: InfoExtractor"""
        self.ie = ie

    def listing(self, id):
        json = self._get_json(VIDEO_LISTING_URL, id)
        return json

    def meta(self, id):
        json = self._get_json(META_URL, id)
        return json

    def info(self, id):
        json = self._get_json(FILE_INFO_URL, id)
        return json

    def context(self, id):
        meta = self.meta(id)
        return meta['context']

    def formats(self, id):
        json = self._get_json(TOKENIZER_URL, id)
        status = json['status']
        if status == 'NOT_PLAYABLE':
            raise ExtractorError("video is not playable")
        if status != 'OK':
            raise ExtractorError("unknown status: %s", status)
        return json['formats']

    def _get_json(self, url, id):
        id = int(id)
        formatted_url = url.format(id=id)
        return self.ie._download_json(formatted_url, id)


class TvpIE(InfoExtractor):
    IE_NAME = 'tvp.pl'
    _VALID_URL = r'https?://(?:vod|www)\.(\w+\.)?tvp\.pl/(?P<id>\d+)/.*'

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

    def _real_initialize(self):
        self.api = TvpApi(self)

    @staticmethod
    def _format_formats(formats, video_id):

        mime_ext = {
            'video/x-ms-wmv': 'wmv',
            'video/mp4': 'mp4'
        }

        viable_formats = []
        for f in formats:
            if f['mimeType'] in IGNORED_MIMETYPES:
                continue

            elif f['mimeType'].startswith('video/'):
                viable_formats.append(
                    {'url': f['url'],
                     'ext': mime_ext.get(f['mimeType'], None),
                     'vbr': f['totalBitrate']})

        return viable_formats

    def _get_video(self, context):
        id = context['material_id']
        if context['title_root']:
            title = context['title_root']
        elif not context['website_title']:
            title = context['title']
        else:
            title = ', '.join([context['website_title'], context['title']])
        url = context['url']
        description = context['description_root']

        try:
            formats = self._format_formats(self.api.formats(id), id)
        except ExtractorError as e:
            self.to_screen("%s: %s" % (title, e))
            raise

        self._sort_formats(formats)

        return {
            'id': str(id),
            'url': url,
            'title': title,
            'description': description,
            'formats': formats,
        }

    def _get_playlist_videos(self, playlist_id):
        ids = [playlist_id]

        while ids:
            item_id = ids.pop()
            listing = self.api.listing(item_id)
            for item in listing['items']:
                if 'directory_video' in item['types']:
                    ids.append(item['_id'])
                if 'video' in item['types'] and item['is_released']:
                    meta = self.api.context(item['_id'])
                    try:
                        yield self._get_video(meta)
                    except ExtractorError:
                        pass

    def _get_playlist(self, context):
        id = context['material_id']
        title = context['title']
        description = context['lead_root']

        return self.playlist_result(self._get_playlist_videos(id),
                                    str(id), title, description)

    def _real_extract(self, url):
        id = self._match_id(url)
        ctx = self.api.context(id)
        if ctx['format_id'] == 0:
            file_info = self.api.info(id)
            original_id = file_info.get('copy_of_object_id')
            if original_id:
                ctx = self.api.context(original_id)

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

    def _real_extract(self, url):
        video_id = self._match_id(url)
        context = self.api.context(video_id)
        return self._get_video(context)
