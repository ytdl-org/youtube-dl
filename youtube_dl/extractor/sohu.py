# encoding: utf-8

import re
import json
import time
import logging
import urllib2

from .common import InfoExtractor
from ..utils import compat_urllib_request, clean_html


class SohuIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.sohu\.com/\d+?/n(?P<id>\d+)\.shtml.*?'

    _TEST = {
        u'url': u'http://tv.sohu.com/20130724/n382479172.shtml#super',
        u'file': u'382479172.flv',
        u'md5': u'cc84eed6b6fbf0f2f9a8d3cb9da1939b',
        u'info_dict': {
            u'title': u'The Illest - Far East Movement Riff Raff',
        },
    }


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        pattern = r'<title>(.+?)</title>'
        compiled = re.compile(pattern, re.DOTALL)
        title = self._search_regex(compiled, webpage, u'video title')
        title = clean_html(title).split('-')[0].strip()
        pattern = re.compile(r'var vid="(\d+)"')
        result = re.search(pattern, webpage)
        if not result:
            logging.info('[Sohu] could not get vid')
            return None
        vid = result.group(1)
        logging.info('vid: %s' % vid)
        base_url_1 = 'http://hot.vrs.sohu.com/vrs_flash.action?vid='
        url_1 = base_url_1 + vid
        logging.info('json url: %s' % url_1)
        webpage = self._download_webpage(url_1, vid)
        json_1 = json.loads(webpage)
        # get the highest definition video vid and json infomation.
        vids = []
        qualities = ('oriVid', 'superVid', 'highVid', 'norVid')
        for vid_name in qualities:
            vids.append(json_1['data'][vid_name])
        clearest_vid = 0
        for i, v in enumerate(vids):
            if v != 0:
                clearest_vid = v
                logging.info('quality definition: %s' % qualities[i][:-3])
                break
        if not clearest_vid:
            logging.warning('could not find valid clearest_vid')
            return None
        if vid != clearest_vid:
            url_1 = '%s%d' % (base_url_1, clearest_vid)
            logging.info('highest definition json url: %s' % url_1)
            json_1 = json.loads(urllib2.urlopen(url_1).read())
        allot = json_1['allot']
        prot = json_1['prot']
        clipsURL = json_1['data']['clipsURL']
        su = json_1['data']['su']
        num_of_parts = json_1['data']['totalBlocks']
        logging.info('Total parts: %d' % num_of_parts)
        base_url_3 = 'http://allot/?prot=prot&file=clipsURL[i]&new=su[i]'
        files_info = []
        for i in range(num_of_parts):
            middle_url = 'http://%s/?prot=%s&file=%s&new=%s' % (allot, prot, clipsURL[i], su[i])
            logging.info('middle url part %d: %s' % (i, middle_url))
            middle_info = urllib2.urlopen(middle_url).read().split('|')
            middle_part_1 = middle_info[0]
            download_url = '%s%s?key=%s' % (middle_info[0], su[i], middle_info[3])

            info = {
                'id': '%s_part%02d' % (video_id, i + 1),
                'title': title,
                'url': download_url,
                'ext': 'mp4',
            }
            files_info.append(info)
            time.sleep(1)
        if num_of_parts == 1:
            info =  files_info[0]
            info['id'] = video_id
            return info
        return files_info
