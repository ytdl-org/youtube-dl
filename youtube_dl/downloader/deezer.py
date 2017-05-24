from Crypto.Cipher import Blowfish
import binascii

from .common import FileDownloader

from ..utils import sanitized_Request

def blowfishDecrypt(data, key):
    """ CBC decrypt data with key """
    c = Blowfish.new(key, Blowfish.MODE_CBC, binascii.a2b_hex("0001020304050607"))
    return c.decrypt(data)


def decryptfile(fh, key, fo):
    """
    Decrypt data from file <fh>, and write to file <fo>.
    decrypt using blowfish with <key>.
    Only every third 2048 byte block is encrypted.
    """
    i = 0
    while True:
        data = fh.read(2048)
        if not data:
            break

        if (i % 3)==0 and len(data)==2048:
            data = blowfishDecrypt(data, key)
        fo.write(data)
        i += 1


class DeezerDownloader(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        request = sanitized_Request(url, None, {})
        data = self.ydl.urlopen(request)

        with open(filename, "wb") as fo:
            decryptfile(data, info_dict['key'], fo)

