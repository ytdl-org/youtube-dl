# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


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

    def _real_extract(self, url):
        """ extract qq video url """
        mobj = re.match(self._VALID_URL, url)
        pid = mobj.group('pid')
        video_id = mobj.group('id') or mobj.group('vid') or pid

        info_doc = self._download_xml(
                'http://vv.video.qq.com/getinfo?vid={0}&otype=xml&defaultfmt=shd'.format(video_id),
                video_id, 'fetch video metadata')

        title = info_doc.find('./vl/vi/ti').text

        if (pid is not None):
            fclip = info_doc.find('./vl/vi/cl/fc').text
            fn = info_doc.find('./vl/vi/fn').text
            vtypes = {v.find('./name').text:v.find('./id').text for v in info_doc.findall('./fl/fi')}
            url = info_doc.findall('./vl/vi/ul/ui/url')[-1].text
            entries = [{
                           'id': '{0}_part{1}'.format(video_id, i + 1),
                           'title': title,
                           'formats': [],
                       } for i in range(int(fclip))]
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
                    'http://vv.video.qq.com/getkey?format=10{0}&otype=xml&vid={1}&filename={2}'.format(int(qid) % 10000, video_id, newfn),
                        video_id, 'get {0}{1} vkey'.format('clip', i + 1))
                vkey = key_doc.find('./key').text
                video_url = '{0}{1}?vkey={2}&type={3}'.format(url, newfn, vkey, 'mp4')
                entries[i]['formats'].append({
                    'url': video_url,
                    'ext': 'mp4',
                })
            return {
                '_type': 'multi_video',
                'id': video_id,
                'title': title,
                'entries': entries,
            }
        else:
            url_doc = self._download_xml(
                    'http://vv.video.qq.com/geturl?vid={0}&otype=xml'.format(video_id),
                    video_id, 'fetch video url')
            url = url_doc.find('./vd/vi/url').text
            ext = self._search_regex('\.([\d\w]+)\?', url, '', '')
            return {
                'id': video_id,
                'title': title,
                'url': url,
                'ext': ext,
            }
