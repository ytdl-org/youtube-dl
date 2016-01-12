# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class QqVideoIE(InfoExtractor):
    """ qq viedo extractor """
    IE_NAME = 'qq'
    IE_DESC = '腾讯'
    # http://v.qq.com/page/9/n/6/9jWRYWGYvn6.html
    # http://v.qq.com/cover/o/oy8cl3wkrebcv8h.html?vid=x001970x491
    # http://v.qq.com/cover/x/xfxd9mej2luhfoz/s00190fcjfl.html 连续剧
    # 普通流视频（完整视频）
    # http://vv.video.qq.com/geturl?vid=v00149uf4ir&otype=json
    # 高清视频（分段视频）
    # 1080P-fhd，超清-shd，高清-hd，标清-sd
    # http://vv.video.qq.com/getinfo?vids=v00149uf4ir&otype=json&charge=0&defaultfmt=shd
    _VALID_URL = r'http://v\.qq\.com/(?:cover/.+?/(?P<pid>[\w\d_-]+)\.html(?:\?vid=(?P<vid>[\w\d_-]+))?' \
                 r'|page/.+?/(?P<id>[\w\d_-]+)\.html)'
    _TESTS = [{
        'url': 'http://v.qq.com/page/9/n/6/9jWRYWGYvn6.html',
        'info_dict': {
            'id': '9jWRYWGYvn6',
            'ext': 'mp4',
            'title': '歼-20试飞63次 国防部指挥例行试验',
        }
    },
        {
            'url': 'http://v.qq.com/cover/o/oy8cl3wkrebcv8h.html?vid=x001970x491',
            'info_dict': {
                'id': 'x001970x491',
                'ext': 'mp4',
                'title': '韩国青瓦台召开紧急会议 国防部加紧检查战备状态',
            },
        },
        {
            'url': 'http://v.qq.com/cover/x/xfxd9mej2luhfoz/s00190fcjfl.html',
            'info_dict': {
                'id': 's00190fcjfl',
                'ext': 'mp4',
                'title': '芈月传_01',
            },
        }

    ]

    def _soap_extract(self, url, video_id):
        """ extract soap opera url of qq video,"""
        webpage = self._download_webpage(url, video_id, 'download web page: {0}'.format(url))
        album_list = [album.group('vid') for album in re.finditer(r'(?is)<a[^>]+class="album_link"\s+id="(?P<vid>[\w\d\-_]+)"[^>]+>.*?</a>', webpage)]
        if len(album_list) == 0:
            raise ExtractorError('invalid video id: {0}'.format(video_id))
        elif video_id in album_list:
            album_list.clear()
            album_list.append(video_id)

        entries = []
        for album_index in range(len(album_list)):
            vid = album_list[album_index]
            info_doc = self._download_xml(
                    'http://vv.video.qq.com/getinfo?vid={0}&otype=xml&defaultfmt=shd'.format(vid),
                    vid, 'fetch video metadata: {0}'.format(vid))
            fclip = info_doc.find('./vl/vi/cl/fc').text
            fn = info_doc.find('./vl/vi/fn').text
            vtypes = {v.find('./name').text:v.find('./id').text for v in info_doc.findall('./fl/fi')}
            base_url = info_doc.findall('./vl/vi/ul/ui/url')[-1].text
            title = info_doc.find('./vl/vi/ti').text
            for i in range(int(fclip)):
                newfn = '{0}.{1}.{2}'.format(fn[:-4], i + 1, 'mp4')
                qid = vtypes['sd']
                if 'fhd' in vtypes:
                    qid = vtypes['fhd']
                elif 'shd' in vtypes:
                    qid = vtypes['shd']
                elif 'hd' in vtypes:
                    qid = vtypes['hd']
                key_doc = self._download_xml(
                        'http://vv.video.qq.com/getkey?format=10{0}&otype=xml&vid={1}&filename={2}'.format(int(qid) % 10000, vid, newfn),
                        vid, 'get {0} {1}{2} vkey with vid: {3}'.format(title, 'clip', i + 1, vid))
                vkey = key_doc.find('./key').text
                video_url = '{0}{1}?vkey={2}&type={3}'.format(base_url, newfn, vkey, 'mp4')
                entries.append({
                    'id': '{0}_part{1}'.format(vid, i + 1),
                    'title': title,
                    'formats': [{
                        'url': video_url,
                        'ext': 'mp4'
                    }],
                })
        return {
            '_type': 'multi_video',
            'id': video_id,
            'title': title,
            'entries': entries,
        }

    def _video_extract(self, url, video_id):
        """ extract normal qq video url """
        video_url = self._download_xml(
                    'http://vv.video.qq.com/geturl?vid={0}&otype=xml'.format(video_id),
                    video_id, 'fetch video url').find('./vd/vi/url').text
        ext = self._search_regex('\.([\d\w]+)\?', video_url, '', '')
        title = self._download_xml(
                'http://vv.video.qq.com/getinfo?vid={0}&otype=xml&defaultfmt=shd'.format(video_id),
                video_id, 'fetch video metadata').find('./vl/vi/ti').text
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': ext,
        }

    def _real_extract(self, url):
        """ extract qq video url """
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('vid') or mobj.group('pid')
        if (mobj.group('pid') is not None):
            return self._soap_extract(url, video_id)
        else:
            return self._video_extract(url, video_id)
