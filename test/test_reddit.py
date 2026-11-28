from __future__ import unicode_literals

import unittest

from test.helper import FakeYDL
from youtube_dl.extractor.reddit import RedditRIE


class _TestRedditRIE(RedditRIE):
    def __init__(self, downloader):
        super(_TestRedditRIE, self).__init__(downloader)
        self.cookies = {}
        self.requests = []
        self.download_kwargs = None
        self.skip_old_session_cookie = False

    def _get_cookies(self, url):
        return self.cookies

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None,
                         fatal=True, data=None, headers={}, query={}, expected_status=None):
        self.requests.append((url_or_request, query))
        if 'old.reddit.com' in url_or_request and not self.skip_old_session_cookie:
            self.cookies['loid'] = object()
        elif '/svc/shreddit/' in url_or_request:
            self.cookies['loid'] = object()
        return True

    def _download_json(self, url, video_id, **kwargs):
        self.download_kwargs = kwargs
        return [{
            'data': {
                'children': [{
                    'data': {
                        'url': 'https://v.redd.it/test-video',
                    },
                }],
            },
        }]

    def _extract_m3u8_formats(self, *args, **kwargs):
        return []

    def _extract_mpd_formats(self, *args, **kwargs):
        return []

    def _sort_formats(self, formats):
        pass


class TestRedditSession(unittest.TestCase):
    def setUp(self):
        self.ie = _TestRedditRIE(FakeYDL())

    def test_initializes_anonymous_session(self):
        result = self.ie._real_extract(
            'https://www.reddit.com/r/videos/comments/abc123/example-post/')

        self.assertEqual(result['url'], 'https://v.redd.it/test-video')
        self.assertEqual(self.ie.requests[0][0], 'https://old.reddit.com/')
        self.assertEqual(self.ie.download_kwargs.get('expected_status'), 403)

    def test_falls_back_to_shreddit_when_old_reddit_does_not_set_loid(self):
        self.ie.skip_old_session_cookie = True
        self.ie._real_extract(
            'https://www.reddit.com/r/videos/comments/abc123/example-post/')

        self.assertEqual(self.ie.requests[0][0], 'https://old.reddit.com/')
        self.assertIn('/svc/shreddit/example-post', self.ie.requests[1][0])
        self.assertEqual(self.ie.requests[1][1]['render-mode'], 'partial')
