# coding: utf-8
from __future__ import unicode_literals

import re

from .brightcove import BrightcoveNewIE


class TVerIE(BrightcoveNewIE):

    _TESTS = [
        {
            'url': 'https://tver.jp/feature/f0057485',  # 'feature'
            'md5': '1c1c09662252571992dee0441028b4ec',  # MD5 hash of a short video downloaded by running youtube-dl with the --test option
            'info_dict': {
                'id': 'f0057485',  # TVer ID
                'display_id': 'ref:hanzawa_naoki---s2----323-001',  # Brightcove ID
                'ext': 'mp4',
                'title': '半沢直樹(新シリーズ)　第1話 子会社VS銀行!飛ばされた半沢の新たな下剋上が始まる',
                'description': '大和田(香川照之)の不正を糾弾し､子会社へ出向を命じられた半沢直樹(堺雅人)は､東京セントラル証券営業企画部長に｡ある日1500億円超の買収案件が舞い込むが…｡',
                'thumbnail': 'https://cf-images.ap-northeast-1.prod.boltdns.net/v1/jit/4031511847001/37b5f176-3989-48d9-81d1-4688e80c5531/main/1920x1080/34m10s16ms/match/image.jpg',
                'duration': 4100.032,
                'timestamp': 1600308623,
                'upload_date': '20200917',
                'uploader_id': '4031511847001',
            },
            'skip': 'Running from test_download.py doesn\'t seem to be able to handle encrypted HLS videos',
        },
        {
            'url': 'https://tver.jp/corner/f0056997',  # 'corner'
            'md5': 'aac4e681dcdb775fc44497da4f7bdd05',  # MD5 hash of a short video downloaded by running youtube-dl with the --test option
            'info_dict': {
                'id': 'f0056997',  # TVer ID
                'display_id': 'ref:kanokari_10',  # Brightcove ID
                'ext': 'mp4',
                'title': '彼女、お借りします　第10話「友達の彼女」-トモカノ-',
                'description': 'バイトの初任給を何に使おうか考える和也だったが、ふと栗林のことが脳裏をよぎる。最近栗林の様子がおかしいと、木部から話を聞いていたのだ。ボーッとしていたり、女性不信のつぶやきをしているという。和也は意を決して、栗林を呼び出すことに。翌日、栗林が和也を待っていると──「駿君、だよね？」。待ち合わせ場所にやって来たのは、千鶴だった……！',
                'thumbnail': 'https://cf-images.ap-northeast-1.prod.boltdns.net/v1/jit/5102072605001/900216cc-2e97-4c19-93bb-1a531de358d6/main/1920x1080/12m18s37ms/match/image.jpg',
                'duration': 1476.075,
                'timestamp': 1599554409,
                'upload_date': '20200908',
                'uploader_id': '5102072605001',
            },
            'skip': 'Running from test_download.py doesn\'t seem to be able to handle encrypted HLS videos',
        },
        {
            'url': 'https://tver.jp/episode/76799350',  # 'episode'
            'md5': 'ad893db02b8a3e949216c463af7ce51e',  # MD5 hash of a short video downloaded by running youtube-dl with the --test option
            'info_dict': {
                'id': '76799350',  # TVer ID
                'display_id': '2366_2365_4533',  # Brightcove ID
                'ext': 'mp4',
                'title': '港時間　#49　神奈川県／リビエラシーボニアマリーナ　9月18日(金)放送分',
                'description': '【毎週金曜 よる12時15分から放送】\n\n日本のヨット文化 を育んできた三浦半島の西海岸、小網代湾にあるリビエラシーボニアマリーナ。昨年から始まったSailGPの日本チームを率いるヨット界のレジェンドに会いました。',
                'thumbnail': 'https://cf-images.ap-northeast-1.prod.boltdns.net/v1/jit/4394098883001/904361ca-40d3-4028-8478-8916b9a0ff49/main/1920x1080/58s80ms/match/image.jpg',
                'duration': 116.16,
                'timestamp': 1600052421,
                'upload_date': '20200914',
                'uploader_id': '4394098883001',
            },
            'skip': 'Running from test_download.py doesn\'t seem to be able to handle encrypted HLS videos',
        },
    ]

    IE_NAME = 'TVer'
    IE_DESC = 'TVer'

    _VALID_URL = r'https?://(?:www\.)?tver\.jp/(corner|episode|feature)/(?P<id>f?[0-9]+)'
    _GEO_COUNTRIES = ['JP']  # TVer service is limited to Japan only

    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/default_default/index.html?videoId=ref:%s'

    def _real_extract(self, url):

        # extract video id
        video_id = self._match_id(url)

        # download webpage
        webpage = self._download_webpage(url, video_id)

        # extract video information
        video_info_csv = self._search_regex(r'addPlayer\((?P<video_info>.*?)\);', webpage, 'video information', flags=re.DOTALL).strip()
        video_info_csv = video_info_csv.replace('\t', '').replace('\n', '').replace('\'', '')  # remove \t and \n and '
        video_info = video_info_csv.split(',')

        # extract brightcove account id
        brightcove_account_id = video_info[3]

        # extract brightcove video id
        brightcove_video_id = video_info[4]

        # brightcove url
        brightcove_url = self.BRIGHTCOVE_URL_TEMPLATE % (brightcove_account_id, brightcove_video_id)

        # debug output
        if self._downloader.params.get('verbose', False):
            self.to_screen('Video Information: %s' % video_info)
            self.to_screen('Brightcove Account ID: %s' % brightcove_account_id)
            self.to_screen('Brightcove Video ID: %s' % brightcove_video_id)
            self.to_screen('Brightcove URL: %s' % brightcove_url)

        # evacuate _VALID_URL
        _VALID_URL = self._VALID_URL

        # temporarily replace _VALID_URL
        # prevent _VALID_URL from being the URL of Tver when executing the parent class's _real_extract () method
        self._VALID_URL = r'https?://players\.brightcove\.net/(?P<account_id>\d+)/(?P<player_id>[^/]+)_(?P<embed>[^/]+)/index\.html\?.*(?P<content_type>video|playlist)Id=(?P<video_id>\d+|ref:[^&]+)'

        # get video information
        info_dict = super(TVerIE, self)._real_extract(brightcove_url)

        # get video description
        description = \
            self._html_search_meta(['description', 'og:description', 'twitter:description'], webpage, 'description', default=None) or \
            self._html_search_regex(r'<div[^>]+class="description"[^>]*>(?P<description>.*?)</div>', webpage, 'description', default=None, flags=re.DOTALL)

        # undo _VALID_URL
        self._VALID_URL = _VALID_URL

        # TVer ID
        info_dict['id'] = video_id
        # Brightcove ID
        info_dict['display_id'] = brightcove_video_id
        # select large thumbnail
        info_dict['thumbnail'] = info_dict.get('thumbnail').replace('160x90', '1920x1080')
        # desctiption
        info_dict['description'] = description

        return info_dict
