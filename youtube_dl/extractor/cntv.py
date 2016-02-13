# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_request

class CntvIE(InfoExtractor):
    IE_NAME = 'cntv'
    IE_DESC = '央视网'
    _VALID_URL = r'''(?x)
        (?:
            http://(?:ent|tv|sports|english|chunwan)\.(?:cntv|cctv)\.(?:com|cn)/
            (?:
                (?:video|special)/(?:[_A-Za-z0-9]+)|(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)
            )
        )
        /(?P<id>[A-Za-z0-9]+)(index)?(?:\.shtml|)
    '''

    _TESTS = [{
        'url': 'http://sports.cntv.cn/2016/02/12/ARTIaBRxv4rTT1yWf1frW2wi160212.shtml',
        'md5': 'd0f8c3e043fe43534517ed47c831fd4e',
        'info_dict': {
            'id': '5ecdbeab623f4973b40ff25f18b174e8',
            'ext': 'flv',
            'title': '[NBA]二少联手砍下46分 雷霆主场击败鹈鹕（快讯）',
            'description': 'md5:7e14a5328dc5eb3d1cd6afbbe0574e95',
            'uploader': 'songjunjie'
        }
    },{
        'url': 'http://tv.cctv.com/2016/02/05/VIDEUS7apq3lKrHG9Dncm03B160205.shtml',
        'md5': '3bde627de65b6bad064f3e67ec9e71a1',
        'info_dict': {
            'id': 'efc5d49e5b3b4ab2b34f3a502b73d3ae',
            'ext': 'flv',
            'title': '[赛车]“车王”舒马赫恢复情况成谜（快讯）',
            'description': '2月4日，蒙特泽莫罗透露了关于“车王”舒马赫恢复情况，但情况是否属实遭到了质疑。',
            'uploader': 'shujun'
        }
    },{
        'url': 'http://english.cntv.cn/special/four_comprehensives/index.shtml',
        'md5': 'f37a56d5f16647eae24c3e618f8d23a2',
        'info_dict': {
            'id': '4bb9bb4db7a6471ba85fdeda5af0381e',
            'ext': 'flv',
            'title': 'NHnews008 ANNUAL POLITICAL SEASON',
            'description': 'Four Comprehensives',
            'uploader': 'zhangyunlei'
        }
    },{
        'url': 'http://ent.cntv.cn/2016/01/18/ARTIjprSSJH8DryTVr5Bx8Wb160118.shtml',
        'md5': '37ad2407b5f28336ddf26aacea570ee5',
        'info_dict': {
            'id': '45336758dd474ef39dc6887f115e0375',
            'ext': 'flv',
            'title': '《爱国之恋》中国梦新歌展播  综艺视频精切',
            'description': 'md5:856836ae2660f000e458ead597b1e2bd',
            'uploader': 'baiyuqing'
        }
    },{
        'url': 'http://tv.cntv.cn/video/C39296/e0210d949f113ddfb38d31f00a4e5c44',
        'md5': 'd7188ecc2a2f8447c70023895724c31c',
        'info_dict': {
            'id': 'e0210d949f113ddfb38d31f00a4e5c44',
            'ext': 'flv',
            'title': '《传奇故事》 20150409 金钱“魔术”（下）',
            'description': '本期节目主要内容：     2014年10月23日凌晨，浙江余杭警方出动2000多名警力，一举摧毁1040阳光工程传销组织，抓获65名涉嫌传销的组织头目，教育遣返400多名参与传销人员。',
            'uploader': '陆银凯'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_id_regex = [r'var guid[ ="]+([a-zA-Z0-9]+)"',
                    r'"videoCenterId"[ ,"]+([a-zA-Z0-9]+)"',
                    r'"changePlayer\(\'([a-zA-Z0-9]+)\'\)\"']
        video_id = self._search_regex(video_id_regex, webpage, 'video_id', default=None)

        if video_id is None:
            video_id = self._match_id(url)

        # refer to youku.py
        def retrieve_data(req_url, note):
            req = compat_urllib_request.Request(req_url)

            cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
            if cn_verification_proxy:
                req.add_header('Ytdl-request-proxy', cn_verification_proxy)

            raw_data = self._download_json(req, video_id, note=note)
            return raw_data

        get_info_url = \
            'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do' + \
            '?pid=%s' % video_id + \
            '&tz=-8' + \
            '&from=000tv' + \
            '&url=%s' % url + \
            '&idl=32' + \
            '&idlr=32' + \
            '&modifyed=false'

        data = retrieve_data(
            get_info_url,
            'Downloading JSON metadata')

        title = data.get('title')
        uploader = data.get('editer_name')
        hls_url = data.get('hls_url')
        formats = self._extract_m3u8_formats(hls_url, video_id, 'flv')
        self._sort_formats(formats)

        description = self._html_search_meta('description', webpage)

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'formats': formats,
            'description': description,
        }
