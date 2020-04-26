from .common import InfoExtractor

LABEL_SIZES={
    '480p': {"width":640, "height": 480},
    '480i': {"width":640, "height": 480},
    '720p': {"width":1280, "height": 720},
    '720i': {"width":1280, "height": 720},
    '1080p': {"width":1920, "height": 1080},
    '1080i': {"width":1920, "height": 1080},
    '1440p': {"width":2560, "height": 1440},
    '1440i': {"width":2560, "height": 1440},
    '4K': {"width":3840, "height": 2160},
    '2160p': {"width":3840, "height": 2160},
    '2160i': {"width":3840, "height": 2160},
    '8K': {"width":7680, "height": 4320},
    '4320p': {"width":7680, "height": 4320},
    '4320i': {"width":7680, "height": 4320},
}

class MyRunningManIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?myrunningman\.com/ep/(?P<id>[0-9]+)$'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        data_url = self._html_search_regex(r'data-url="f([^"]+)"', webpage, "data-url")
        source = self._download_json('https://feurl.com/api/source/{}'.format(data_url),video_id, data='r=https%3A%2F%2Fwww.myrunningman.com%2Fcache%2Fstream%2Ff{}.html&d=feurl.com'.format(data_url).encode('utf-8'))
        assert source['success']

        formats = []
        for d in source['data']:
            formats.append(dict({
                'ext': d['type'],
                'url': d['file'],
            }, **LABEL_SIZES.get(d['label'], {})))

        return {
            'id': video_id,
            'title': self._html_search_regex(
                r'<title>(?:Episode #[0-9]+ - )?(.*?)(?: - My Running Man [(]MyRM[)])?</title>',
                webpage,
                'title'
            ),
            'formats': formats,
        }


_="""{
  "success": true,
  "player": {
    "poster_file": "/userdata/220521/poster/4/0o/40ox-ry0yo8.png?v=1558638851",
    "logo_file": "/userdata/220521/player/2706_logo.png?v=1558807686",
    "logo_position": "control-bar",
    "logo_link": "https://www.myrunningman.com",
    "logo_margin": 10,
    "aspectratio": "16:9",
    "powered_text": "Fembed 1.6.0",
    "powered_url": "https://www.fembed.com",
    "css_background": "rgba(0, 0, 0, 0)",
    "css_text": "#f2f2f2",
    "css_menu": "#333333",
    "css_mntext": "#ffffff",
    "css_caption": "#000000",
    "css_cttext": "#ffffff",
    "css_ctsize": "15",
    "css_ctopacity": "40",
    "css_icon": "rgba(255, 255, 255, 0.8)",
    "css_ichover": "#ffffff",
    "css_tsprogress": "#f2f2f2",
    "css_tsrail": "rgba(255, 255, 255, 0.3)",
    "css_button": "#565656",
    "css_bttext": "#ffffff",
    "opt_autostart": false,
    "opt_title": false,
    "opt_quality": true,
    "opt_caption": false,
    "opt_download": false,
    "opt_sharing": false,
    "opt_playrate": false,
    "opt_mute": false,
    "opt_loop": false,
    "opt_vr": false,
    "opt_cast": {
      "appid": "00000000"
    },
    "opt_nodefault": false,
    "opt_forceposter": false,
    "opt_parameter": false,
    "restrict_domain": "myrunningman.com",
    "restrict_action": "DisplayErrorPage",
    "restrict_target": "https://www.myrunningman.com/",
    "adb_enable": false,
    "adb_offset": "0",
    "adb_text": "Please turn off adblockers in order to continue watching",
    "ads_adult": false,
    "ads_pop": true,
    "ads_vast": true,
    "ads_free": 0,
    "trackingId": "",
    "viewId": "",
    "income": false,
    "incomePop": false,
    "resume_text": "Welcome back! You left off at xx:xx:xx. Would you like to resume watching?",
    "resume_yes": "Yes",
    "resume_no": "No",
    "resume_enable": true,
    "css_ctedge": "none",
    "logger": "https://v3.fstats.xyz",
    "revenue": "https://b.suggestvideos.xyz/scripts/coming-soon",
    "revenue_fallback": "https://obefjbb4mykw.com/6b/64/32/6b64325728db266a83a1ce720563f755.js",
    "revenue_track": "https://mc.yandex.ru/watch/56313682"
  },
  "data": [
    {
      "file": "https://fvs.io/redirector?token=VXIxalFMbFBKZE5zOVRvNjVNVWxNYkxXR2dCdis5V2xtL3lVR2E2VGxEdmVraSs4YXp2Q0MzeWJFMDA0bDhJK2ZlWDlBTlF3eTI3dXVqWWl4aHlOTHEvVkpMNHYveHRtWGhCc08xWlFZVGx3MjBaSHIrT3ZvODRZM2FZU21GaUZ2WEE0Vm00cHBpazFHcGcxaTB0Vzc3MmZ1QWs9OnZNVFkzWTdWdm02RGc1Tm9hd1M0ZEE9PQ",
      "label": "480p",
      "type": "mp4"
    },
    {
      "file": "https://fvs.io/redirector?token=NUh5RHFiR2lUUWswcXFFUEhCLzhIUk90Z0JoRWhQb21ERGJBSGhEU2RxWFhvSS9rbDRKeW4vVkRMd0RrTWlFNkYyMUU5ZGN3cmEyVWFCeVdpTGJueDl3cC9hOWF2RkY4Y2ZpYmZzeGE5c2N2NUdPWVpoc21RMUE3R0ZPU3RqY0VoTWZLQTUwMkxFTnMwZTkreVpoNzYrQnVYdz09OmZ4UlF1eFNkU3ZYT3RzOGcrZ0k3TlE9PQ",
      "label": "720p",
      "type": "mp4"
    }
  ],
  "captions": [],
  "is_vr": false
}"""
