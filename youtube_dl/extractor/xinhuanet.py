# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

#================================#
# 新华网视频 youtube-dl 下载扩展 #
#================================#

"""
#
# 使用前须知：
# 该脚本需要预装 youtube-dl 下载器，推荐用 pip3 install youtube-dl 安装
# 1.使用该脚本时请将该脚本放入脚本库 youtube_dl/extractor 文件夹下
# 2.请找到 youtube_dl/extractor 文件夹下的 extractors.py 文件
#   在最后添加一行内容 from .xinhuanet import XinHuaNetIE,XinHuaNet2IE
# *另外请使用 python3，避免出现一些比较低级的麻烦。
#
# 解析网页说明：
# 该脚本解析 http://www.xinhuanet.com 的两种视频页
# 第一种：http://www.xinhuanet.com/video/2018-08/28/c_129941452.htm（新闻页）
# 第二种：http://vod.xinhuanet.com/v/vod.html?vid=536626（通用地址）
# 其中第二种为通用视频地址，第一种页面内嵌套第二种地址
#
# *不重要的说明：
# 工具主要用于新华网视频下载，主要是视频下载，所以，就对一般爬虫而言，
# 即便出现第一种网页也会在第一种网页内搜集到第二种网页地址作为该网页的视频地址进行统一，也方便去重
# 所以这里即便有对第一种网页实现下载功能，这也只是一种并不是很有必要的扩展，不过说不定以后别人什么时候也能用上
# 毕竟新闻的比重很多，而且解析也比第二种要方便
#
# 指定存放文件地址方法：
# youtube-dl 如果想要指定文件存放地址的话，请使用它的命令行语法：%()s
# eg. > youtube-dl -o "./video/%(id)s.%(ext)s" http://vod.xinhuanet.com/v/vod.html?vid=536626
# 例如上面这行命令会将视频下载到当前路径的video目录下面并且用 532276.mp4 文件名存放
# 目前我知道的 %()s 语法内必然存在的有 id title ext。 id title是在函数内算出的，详细看函数即可，
# 文件扩展名（ext）是工具自动算出来的
#
"""



class XinHuaNetIE(InfoExtractor):
    IE_NAME = 'xinhuanet'
    IE_DESC = 'xinhuanet video downloader.'
    _VALID_URL = 'http://vod\.xinhuanet\.com/v/vod\.html\?vid=\d+'

    #==================#
    # 通用地址视频下载 #
    #==================#
    # eg. http://vod.xinhuanet.com/v/vod.html?vid=536626
    def _real_extract(self, url):
        def get_real_url_by_simple_url(self, url):
            def _mk_gcid_url(url):
                u = 'http://vod.xinhuanet.com/vod_video_js/%d/%d.js'
                v = int(url.rsplit('=')[1])
                uid = str(v)
                v = u % (int(v/1000),v) 
                # 混肴后的js源代码里面的函数方法：
                # 源代码："http://vod.xinhuanet.com/vod_video_js/"+Math.floor(parseInt(a)/1E3)+"/"+a+".js";
                # 源代码里面的 a 代表了该视频页的数字vid。 通过这个地址进一步获取 gcid 信息后续再继续处理。
                return v,uid

            gurl, uid = _mk_gcid_url(url)
            page = self._download_webpage(gurl, uid)
            gcid = re.findall('http://pubnet.xinhuanet.net:8080/40/([^/]{40})',page)

            if gcid: gcid = gcid[0].upper()
            else: return 'gcid failed,'+gurl,None

            # 通过 gcid 拼接下面的地址可以获取到一些类似js脚本的HTML文本，里面有真实的视频url地址信息
            url = 'http://p2s.xinhuanet.com/getCdnresource_flv?gcid=' + gcid
            page = self._download_webpage(url, uid)
            vurl = re.findall('{ip:"([^"]+)",port:(\d+),path:"([^"]+)"}',page)

            if vurl: vurl = vurl[0]
            else: return 'get realurl failed,'+url,None

            def _get_real_url(vurl):
                # 对通过 gcid 获取的文本找到的信息拼接视频真实 url.
                # vurl 数据样例： ('vodfile12.news.cn', '8080', '/data/cdn_transfer/5C/FB/5cf3d08723ca6a481eb81a572505af7dcca381fb.mp4')
                # 这里没有使用port参数原因是测试得出的结论（8080端口无法使用，用默认80端口就能获取视频，所以不需要使用该port）
                url = 'http://' + vurl[0] + '/' + vurl[2]
                return url
            return uid, _get_real_url(vurl)
        uid, url = get_real_url_by_simple_url(self, url)

        # 对于 youtube-dl 工具而言，该函数返回的参数是一个字典，至少要包括 id，title，url 这三个key的字典。工具会通过这个视频真实url进行下载。
        # 另外，通过给与的url: http://.../vod.html?vid=532276 这个视频地址无法获取更多视频详细信息，甚至连标题信息都没有
        # 所以我把 title和 id都赋值为uid了，下载文件的名字默认为 "%s-%s" % (id, title)
        # eg. http://vod.xinhuanet.com/v/vod.html?vid=532276 这个地址会下载到文件名字为 "532276-532276.mp4" 的视频文件
        if url:
            return {
                'id':       uid,
                'title':    uid,
                'url':      url,
            }
        else:
            # 如果获取真实url失败，则我写的代码里，uid里面回传了简单的错误信息
            # 主要可能是视频不存在了，如果有其他异常可能是正则匹配问题，会打印一下问题出现的地址
            print(uid)


class XinHuaNet2IE(InfoExtractor):
    IE_NAME = 'xinhuanet'
    IE_DESC = 'xinhuanet video downloader.'
    _VALID_URL = 'https?://www\.xinhuanet\.com/video/[^/]+/[^/]+/(?P<id>[^\.]+)\.htm'

    #================#
    # 新闻页视频下载 #
    #================#
    # eg. http://www.xinhuanet.com/video/2018-08/28/c_129941452.htm
    def _real_extract(self, url):
        # 原本计划是从该新闻页面找到嵌套在里面的视频页，然后通过视频页解析方法进一步获取真实地址的
        # 结果发现该页面上直接包含了真实的视频url地址，这设计很真实。真实~ 实在是太真实了~，连跳板都省了。
        m = re.match(self._VALID_URL, url)
        uid = m.group('id')
        page = self._download_webpage(url,uid)
        r_uid = re.findall('http://vod\.xinhuanet\.com/v/vod\.html\?vid=(\d+)',page)
        r_url = re.findall('(?:vodfile)[^<]+(?:mp4)',page)
        if r_uid and r_url:
            uid,url = r_uid[0],'http://' + r_url[0]
            return {
                'id':       uid,
                'title':    uid,
                'url':      url,
            }
        else:
            print("failed download.", url)
