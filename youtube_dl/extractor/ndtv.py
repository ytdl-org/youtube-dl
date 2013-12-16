import re

from .common import InfoExtractor
from ..utils import month_by_name


class NDTVIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?ndtv\.com/video/player/[^/]*/[^/]*/(?P<id>[a-z0-9]+)'

    _TEST = {
        u"url": u"http://www.ndtv.com/video/player/news/ndtv-exclusive-don-t-need-character-certificate-from-rahul-gandhi-says-arvind-kejriwal/300710",
        u"file": u"300710.mp4",
        u"md5": u"39f992dbe5fb531c395d8bbedb1e5e88",
        u"info_dict": {
            u"title": u"NDTV exclusive: Don't need character certificate from Rahul Gandhi, says Arvind Kejriwal",
            u"description": u"In an exclusive interview to NDTV, Aam Aadmi Party's Arvind Kejriwal says it makes no difference to him that Rahul Gandhi said the Congress needs to learn from his party.",
            u"upload_date": u"20131208",
            u"duration": 1327,
            u"thumbnail": u"http://i.ndtvimg.com/video/images/vod/medium/2013-12/big_300710_1386518307.jpg",
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        filename = self._search_regex(
            r"__filename='([^']+)'", webpage, u'video filename')
        video_url = (u'http://bitcast-b.bitgravity.com/ndtvod/23372/ndtv/%s' %
                     filename)

        duration_str = filename = self._search_regex(
            r"__duration='([^']+)'", webpage, u'duration', fatal=False)
        duration = None if duration_str is None else int(duration_str)

        date_m = re.search(r'''(?x)
            <p\s+class="vod_dateline">\s*
                Published\s+On:\s*
                (?P<monthname>[A-Za-z]+)\s+(?P<day>[0-9]+),\s*(?P<year>[0-9]+)
            ''', webpage)
        upload_date = None
        assert date_m
        if date_m is not None:
            month = month_by_name(date_m.group('monthname'))
            if month is not None:
                upload_date = '%s%02d%02d' % (
                    date_m.group('year'), month, int(date_m.group('day')))

        description = self._og_search_description(webpage)
        READ_MORE = u' (Read more)'
        if description.endswith(READ_MORE):
            description = description[:-len(READ_MORE)]

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': duration,
            'upload_date': upload_date,
        }
