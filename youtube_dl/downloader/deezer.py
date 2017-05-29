from __future__ import unicode_literals

from ..blowfish import blowfish_cbc_decrypt
from .common import FileDownloader
from ..utils import sanitized_Request
import time


def decryptfile(fh, key, fo, progress, data_len):
    """
    Decrypt data from file <fh>, and write to file <fo>.
    decrypt using blowfish with <key>.
    Only every third 2048 byte block is encrypted.
    """
    i = 0
    byte_counter = 0
    tstart = time.time()
    while True:
        data = fh.read(2048)
        if not data:
            break

        if (i % 3) == 0 and len(data) == 2048:
            data = blowfish_cbc_decrypt(data, key, b"\x00\x01\x02\x03\x04\x05\x06\x07")
        fo.write(data)
        i += 1

        byte_counter += len(data)

        progress._hook_progress({
            'status': 'downloading',
            'downloaded_bytes': byte_counter,
            'total_bytes': data_len,
            'eta': progress.calc_eta(tstart, time.time(), data_len, byte_counter),
            'speed': progress.calc_speed(tstart, time.time(), byte_counter),
        })


class DeezerDownloader(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        request = sanitized_Request(url, None, {})
        data = self.ydl.urlopen(request)

        with open(filename, "wb") as fo:
            decryptfile(data, info_dict['key'], fo, self, int(data.info().get('Content-length', 0)))
