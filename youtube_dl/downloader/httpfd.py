from .http import HttpFD

import urllib.request as compat_urllib_request
import threading


class HttpHB(HttpFD):
    def real_download(self, filename, info_dict):
        result = False
        if 'heartbeat_url'in info_dict:
            def heart_beat():
                try:
                    data = info_dict['heartbeat_data'].encode("utf-8")
                    compat_urllib_request.urlopen(url=info_dict['heartbeat_url'], data=data)
                    print('heart beat!')
                except Exception as ex:
                    print('heart beat fail: ' + ex.message)
                    pass

                if not result:
                    timer = threading.Timer(25, heart_beat)
                    timer.start()

            heart_beat()

        result = super(HttpHB, self).real_download(filename, info_dict)
        return result
