from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ParliamentLiveUKIE(InfoExtractor):
    IE_NAME = 'parliamentlive.tv'
    IE_DESC = 'UK parliament videos'
    _VALID_URL = r'https?://www\.parliamentlive\.tv/Main/Player\.aspx\?(?:[^&]+&)*?meetingId=(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://www.parliamentlive.tv/Main/Player.aspx?meetingId=15121&player=windowsmedia',
        'info_dict': {
            'id': '15121',
            'ext': 'asf',
            'title': 'hoc home affairs committee, 18 mar 2014.pm',
            'description': 'md5:033b3acdf83304cd43946b2d5e5798d1',
        },
        'params': {
            'skip_download': True,  # Requires mplayer (mms)
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        asx_url = self._html_search_regex(
            r'embed.*?src="([^"]+)" name="MediaPlayer"', webpage,
            'metadata URL')
        asx = self._download_xml(asx_url, video_id, 'Downloading ASX metadata')
        video_url = asx.find('.//REF').attrib['HREF']

        title = self._search_regex(
            r'''(?x)player\.setClipDetails\(
                (?:(?:[0-9]+|"[^"]+"),\s*){2}
                "([^"]+",\s*"[^"]+)"
                ''',
            webpage, 'title').replace('", "', ', ')
        description = self._html_search_regex(
            r'(?s)<span id="MainContentPlaceHolder_CaptionsBlock_WitnessInfo">(.*?)</span>',
            webpage, 'description')

        return {
            'id': video_id,
            'ext': 'asf',
            'url': video_url,
            'title': title,
            'description': description,
        }
