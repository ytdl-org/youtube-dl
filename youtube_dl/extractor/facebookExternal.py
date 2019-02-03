# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote
)


class FacebookExternalExtractorIE(InfoExtractor):
    _VALID_URL = r'(?:https?:\/\/(?:[\w-]+\.)?)(?:facebook\.com|facebookcorewwwi\.onion)\/' \
                 r'(?:[^#]*?\#!\/)?(?:flx\/warn\/)\?(?:.*?)(?:u)=' \
                 r'(?P<id>https?:\/\/.*)'
    _TEST = {
        'url': 'https://www.facebook.com/flx/warn/?u=https://ok.ru/video/1274065521345&h=AT3HvDHvyYWmq_d0apMYHov1W3DmbiVyGLy7QUWYAxXoeMj60gBcYsW4kOu-gXSiEBHk1fVDrlBN3rNOY0E4IDK3TBL7mSvCWLRXv3yZwkS2_7VbmH-1J0jH0B0XMx76PvCf712QltvoUSgqLFJhQ_FSlGGM44FJP_o-NsrNAvJedRrBuw0gyUYcToZvwK8utMr9Z-GESj6tP9fX9xlDChvO7IhAkq9cC3D_naj5ZksqroGkMIbFIfZBqgkZdd0d4657j3awFeHQqItiPGg3D26F47L6RHmrJ9CJGwX01QvtgKlu61N53Kz3jAzbZsGrdlogrEuXX3Y_zeIwZaXfNx_Qz1X4Ub7CqS2ePfLZd6ez01srCR_1pq-HPxOGB79ybz4e54QsF47O-nGgXqm793wtB8w42T_WPUIw1fePBfRrDg3g_UnC1mGVR_1x-dt3RQFrDKrclNk-k_2cqrCpiZ1X3hPFtkNM3HOQYJgVI-1mczqmV3Afx--MjndNXd8Oi19Wu2J_hDqinhH50bYOAF6Ucftn35DCZckV5TC8SP1w8mjB-czyWdgSSv9hWOb_wOZXVnmqpzOuyjvxeKKKYXcCgAp3CoTjNMDzJB5olLmxqMFecR1XlxE2iH9_lM0wABtfQl_gGJa_wh65Y2e75w&_fb_noscript=1',
        'info_dict': {
            'id': '1274065521345',
            'ext': 'mp4',
            'title': 'Az élet dallama 14. rész'
        }
    }

    def _real_extract(self, url):
        # The only role for this extractor would be to pull
        # the redirect URL and to pass that to youtubeDL class
        return self.url_result(
            compat_urllib_parse_unquote(self._match_id(url)))
