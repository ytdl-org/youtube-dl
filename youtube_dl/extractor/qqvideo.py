# coding: utf-8
from __future__ import unicode_literals

import re
import os.path

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
    # http://v.qq.com/cover/x/xfxd9mej2luhfoz
    # 普通流视频（完整视频）
    # http://vv.video.qq.com/geturl?vid=v00149uf4ir&otype=json
    # 高清视频（分段视频）
    # 1080P-fhd，超清-shd，高清-hd，标清-sd
    # http://vv.video.qq.com/getinfo?vids=v00149uf4ir&otype=json&charge=0&defaultfmt=shd
    _VALID_URL = r'http://v\.qq\.com/(?:cover/.+?/(?P<sid>[\w\d_-]+)\.html(?:\?vid=(?P<vid>[\w\d_-]+))?' \
                 r'|page/.+?/(?P<pid>[\w\d_-]+)\.html)'
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

    def _multi_part_video(self, video_id):
        platform = 11
        # hd
        album_hd_xml = self._download_xml(
                'http://vv.video.qq.com/getinfo?vids={0}&platform={1}&charge=0&otype=xml&defaultfmt=hd'.format(
                        video_id, platform),
                video_id, 'get hd video metadata: {0}'.format(video_id))
        # shd
        album_shd_xml = self._download_xml(
                'http://vv.video.qq.com/getinfo?vids={0}&platform={1}&charge=0&otype=xml&defaultfmt=shd'.format(
                        video_id, platform),
                video_id, 'get shd video metadata: {0}'.format(video_id))

        title = album_hd_xml.find('./vl/vi/ti').text

        entries = []
        hd_vtypes = {v.find('./name').text: v.find('./id').text for v in album_hd_xml.findall('./fl/fi')}
        hd_fclip = int(album_hd_xml.find('./vl/vi/cl/fc').text)
        hd_filename = album_hd_xml.find('./vl/vi/fn').text
        hd_base_url = album_hd_xml.findall('./vl/vi/ul/ui/url')[-1].text
        ext = os.path.splitext(hd_filename)[1][1:]

        for i in range(hd_fclip):
            clip_filename = '{0}.{1}.{2}'.format(hd_filename[:-4], i + 1, ext)
            key_xml = self._download_xml(
                    'http://vv.video.qq.com/getkey?otype=xml&format=10{0}&filename={1}&linkver=2&vid={2}&charge=0&platform={3}'.format(
                            int(hd_vtypes['hd']) % 10000, clip_filename, video_id, platform),
                    video_id, 'get {0} {1}{2} vkey with vid: {3}'.format(title, 'clip', i + 1, video_id))
            vkey = key_xml.find('./key').text
            level = key_xml.find('./level').text
            sp = key_xml.find('./sp').text
            vbr = int(album_hd_xml.find('./vl/vi/br').text)
            clipsize = int(album_hd_xml.findall('./vl/vi/cl/ci')[i].find('./cs').text)
            video_url = '{0}{1}?sdtfrom=v1001&vkey={2}&type={3}&level={4}&platform={5}&br={6}&fmt=hd&sp={7}&size={8}'.format(
                hd_base_url, clip_filename, vkey, ext, level, platform, vbr, sp, clipsize)
            entries.append({
                'id': '{0}_part{1}'.format(video_id, i + 1),
                'title': title,
                'formats': [{
                    'url': video_url,
                    'ext': ext,
                    'filesize': clipsize,
                    'vbr': vbr,
                    'width': int(album_hd_xml.find('./vl/vi/vw').text),
                    'height': int(album_hd_xml.find('./vl/vi/vh').text),
                    'quality': 0,
                }]
            })

        shd_vtypes = {v.find('./name').text: v.find('./id').text for v in album_shd_xml.findall('./fl/fi')}
        shd_fclip = album_shd_xml.find('./vl/vi/cl/fc').text
        shd_filename = album_shd_xml.find('./vl/vi/fn').text
        shd_base_url = album_shd_xml.findall('./vl/vi/ul/ui/url')[-1].text
        for i in range(int(shd_fclip)):
            clip_filename = '{0}.{1}.{2}'.format(shd_filename[:-4], i + 1, ext)
            key_xml = self._download_xml(
                    'http://vv.video.qq.com/getkey?otype=xml&format=10{0}&filename={1}&linkver=2&vid={2}&charge=0&platform={3}'.format(
                            int(shd_vtypes['shd']) % 10000, clip_filename, video_id, platform),
                    video_id, 'get {0} {1}{2} vkey with vid: {3}'.format(title, 'clip', i + 1, video_id))
            vkey = key_xml.find('./key').text
            level = key_xml.find('./level').text
            sp = key_xml.find('./sp').text
            vbr = int(album_shd_xml.find('./vl/vi/br').text)
            clipsize = int(album_shd_xml.findall('./vl/vi/cl/ci')[i].find('./cs').text)
            video_url = '{0}{1}?sdtfrom=v1001&vkey={2}&type={3}&level={4}&platform={5}&br={6}&fmt=hd&sp={7}&size={8}'.format(
                shd_base_url, clip_filename, vkey, ext, level, platform, vbr, sp, clipsize)
            format_item = {
                'url': video_url,
                'ext': ext,
                'filesize': clipsize,
                'vbr': vbr,
                'width': int(album_shd_xml.find('./vl/vi/vw').text),
                'height': int(album_shd_xml.find('./vl/vi/vh').text),
                'quality': 1,
            }
            if i < hd_fclip:
                entries[i]['formats'].append(format_item)
            else:
                entries.append({
                    'id': '{0}_part{1}'.format(video_id, i + 1),
                    'title': title,
                    'formats': [format_item]
                })

        return entries

    def _single_video(self, video_id):
        mobile_xml = self._download_xml(
                'http://vv.video.qq.com/getinfo?vids={0}&platform=2'
                '&charge=0&otype=xml&defaultfmt=msd'.format(video_id),
                video_id, 'get video metadata of mobile resolution: {0}'.format(video_id))
        sd_xml = self._download_xml(
                'http://vv.video.qq.com/getinfo?vids={0}&platform=2'
                '&charge=0&otype=xml&defaultfmt=mp4'.format(video_id),
                video_id, 'get video metadata of sd resolution: {0}'.format(video_id))
        mobile_filename = mobile_xml.find('./vl/vi/fn').text
        sd_filename = sd_xml.find('./vl/vi/fn').text
        return {
            'id': '{0}'.format(video_id),
            'title': mobile_xml.find('./vl/vi/ti').text,
            'formats': [{
                'url': '{0}{1}?vkey={2}'.format(mobile_xml.findall('./vl/vi/ul/ui/url')[-1].text, mobile_filename,
                                                mobile_xml.find('./vl/vi/fvkey').text),
                'ext': os.path.splitext(mobile_filename)[1][1:],
                'filesize': int(mobile_xml.find('./vl/vi/fs').text),
                'vbr': int(mobile_xml.find('./vl/vi/br').text),
                'width': int(mobile_xml.find('./vl/vi/vw').text),
                'height': int(mobile_xml.find('./vl/vi/vh').text),
                'quality': -2,
            }, {
                'url': '{0}{1}?vkey={2}'.format(sd_xml.findall('./vl/vi/ul/ui/url')[-1].text, sd_filename,
                                                sd_xml.find('./vl/vi/fvkey').text),
                'ext': os.path.splitext(sd_filename)[1][1:],
                'filesize': int(sd_xml.find('./vl/vi/fs').text),
                'vbr': int(sd_xml.find('./vl/vi/br').text),
                'width': int(sd_xml.find('./vl/vi/vw').text),
                'height': int(sd_xml.find('./vl/vi/vh').text),
                'quality': -1,
            }],
        }

    def _soap_extract(self, url, video_id):
        """ extract soap opera url of qq video,"""
        webpage = self._download_webpage(url, video_id, 'download web page: {0}'.format(url))
        album_list = [album.group('vid') for album in
                      re.finditer(r'(?is)<a[^>]+class="album_link"\s+id="(?P<vid>[\w\d\-_]+)"[^>]+>.*?</a>', webpage)]
        if len(album_list) == 0:
            raise ExtractorError('invalid video id: {0}'.format(video_id))
        elif video_id in album_list:
            album_list.clear()
            album_list.append(video_id)

        # interface
        # mobile
        # http://vv.video.qq.com/getinfo?vids=s00190fcjfl&platform=2&charge=0&otype=xml
        # sd
        # http://vv.video.qq.com/getinfo?vids=s00190fcjfl&platform=2&charge=0&otype=xml&defaultfmt=mp4
        # getvinfo
        # http://vv.video.qq.com/getinfo?vids=s00190fcjfl&platform=11&charge=0&otype=xml&defaultfmt=shd&defnpayver=1
        # getvkey
        # http://vv.video.qq.com/getkey?otype=xml&format=10401&filename=h00197yddy9%2Ep401%2E1%2Emp4&linkver=2&vid=s00190fcjfl&charge=0&platform=11
        # video_url
        # http://video.dispatch.tc.qq.com/h00197yddy9.p401.1.mp4?sdtfrom=v1001&type=mp4&vkey=C0E385B593A13951BBAF7F37D45730E4354E5F5FAE2265F8A395EB42ECE3F98D3EB4E0834B9E8BD3BE0660B774D0F41CE8E4476107D2C247056CCEAF1EC2E36CE8AF34BC1110269DA0B1A598001AE04D6CD90D56EF6EEDBA&level=0&platform=11&br=169&fmt=shd&sp=0&size=68593491

        entries = []
        for album_index in range(len(album_list)):
            vid = album_list[album_index]
            # mobile and sd video
            entries.append(self._single_video(vid))
            # hd and shd video
            for v in self._multi_part_video(vid):
                entries.append(v)
        return {
            '_type': 'multi_video',
            'id': video_id,
            'title': entries[0]['title'],
            'entries': entries,
        }

    def _video_extract(self, url, video_id):
        """ extract normal qq video url """
        video_url = self._download_xml(
                'http://vv.video.qq.com/geturl?vid={0}&otype=xml'.format(video_id),
                video_id, 'fetch video url').find('./vd/vi/url').text
        ext = self._search_regex('\.([\d\w]+)\?', video_url, '', '')
        title = self._download_xml(
                'http://vv.video.qq.com/getinfo?vid={0}&otype=xml'.format(video_id),
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
        video_id = mobj.group('pid') or mobj.group('vid') or mobj.group('sid')
        if (mobj.group('vid') or mobj.group('pid')):
            return self._video_extract(url, video_id)
        else:
            return self._soap_extract(url, video_id)
