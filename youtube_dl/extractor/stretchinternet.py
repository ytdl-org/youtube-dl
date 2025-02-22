from __future__ import unicode_literals

from .common import InfoExtractor
from datetime import datetime
try:
    from zoneinfo import ZoneInfo as compat_ZoneInfo  # Python 3.9+
except ImportError:
    compat_ZoneInfo = None  # Fallback: Do not handle alphabetic time zones

from ..utils import unified_timestamp, parse_iso8601

class StretchInternetIE(InfoExtractor):
    _VALID_URL = r'https?://portal\.stretchinternet\.com/[^/]+/(?:portal|full)\.htm\?.*?\beventId=(?P<id>\d+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        media_url = self._download_json(
            'https://core.stretchlive.com/trinity/event/tcg/' + video_id,
            video_id)[0]['media'][0]['url']

        event = self._download_json(
            'https://neo-client.stretchinternet.com/portal-ws/getEvent.json',
            video_id, query={'eventID': video_id, 'token': 'asdf'})['event']

        return {
            'id': video_id,
            'title': event['title'],
            'timestamp': self._parse_date(event.get('dateTimeString')),
            'url': 'https://' + media_url,
            'uploader_id': event.get('ownerID'),
        }

    def _parse_date(self, date_string):
        """Parses an ISO 8601 date string into a UNIX timestamp."""
        if not date_string:
            return None

        # Attempt to use built-in utils first
        timestamp = unified_timestamp(date_string) or parse_iso8601(date_string)
        if timestamp is not None:
            return timestamp

        try:
            # Manually parse ISO 8601 datetime string with numeric timezone offset
            dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
            return int(dt.timestamp())  # Convert to UNIX timestamp
        except ValueError:
            self._downloader.report_warning(f"Could not parse date string: {date_string}")

        return None
