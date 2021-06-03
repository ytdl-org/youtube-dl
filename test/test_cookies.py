import unittest

from youtube_dl import cookies
from youtube_dl.cookies import LinuxChromeCookieDecryptor, WindowsChromeCookieDecryptor, CRYPTO_AVAILABLE, \
    MacChromeCookieDecryptor


class MonkeyPatch:
    def __init__(self, module, name, temp_value):
        self._module = module
        self._name = name
        self._temp_value = temp_value
        self._backup_value = None

    def __enter__(self):
        self._backup_value = getattr(self._module, self._name)
        setattr(self._module, self._name, self._temp_value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(self._module, self._name, self._backup_value)


@unittest.skipIf(not CRYPTO_AVAILABLE, 'cryptography library not available')
class TestCookies(unittest.TestCase):
    def test_chrome_cookie_decryptor_linux_derive_key(self):
        key = LinuxChromeCookieDecryptor.derive_key('abc')
        assert key == b'7\xa1\xec\xd4m\xfcA\xc7\xb19Z\xd0\x19\xdcM\x17'

    def test_chrome_cookie_decryptor_mac_derive_key(self):
        key = MacChromeCookieDecryptor.derive_key('abc')
        assert key == b'Y\xe2\xc0\xd0P\xf6\xf4\xe1l\xc1\x8cQ\xcb|\xcdY'

    def test_chrome_cookie_decryptor_linux_v10(self):
        with MonkeyPatch(cookies, '_get_linux_keyring_password', lambda *args, **kwargs: ''):
            encrypted_value = b'v10\xccW%\xcd\xe6\xe6\x9fM" \xa7\xb0\xca\xe4\x07\xd6'
            value = 'USD'
            decryptor = LinuxChromeCookieDecryptor('Chrome')
            assert decryptor.decrypt(encrypted_value) == value

    def test_chrome_cookie_decryptor_linux_v11(self):
        with MonkeyPatch(cookies, '_get_linux_keyring_password', lambda *args, **kwargs: ''):
            encrypted_value = b'v11#\x81\x10>`w\x8f)\xc0\xb2\xc1\r\xf4\x1al\xdd\x93\xfd\xf8\xf8N\xf2\xa9\x83\xf1\xe9o\x0elVQd'
            value = 'tz=Europe.London'
            decryptor = LinuxChromeCookieDecryptor('Chrome')
            assert decryptor.decrypt(encrypted_value) == value

    def test_chrome_cookie_decryptor_windows_v10(self):
        with MonkeyPatch(cookies, '_get_windows_v10_password',
                         lambda *args, **kwargs: b'Y\xef\xad\xad\xeerp\xf0Y\xe6\x9b\x12\xc2<z\x16]\n\xbb\xb8\xcb\xd7\x9bA\xc3\x14e\x99{\xd6\xf4&'):
            encrypted_value = b'v10T\xb8\xf3\xb8\x01\xa7TtcV\xfc\x88\xb8\xb8\xef\x05\xb5\xfd\x18\xc90\x009\xab\xb1\x893\x85)\x87\xe1\xa9-\xa3\xad='
            value = '32101439'
            decryptor = WindowsChromeCookieDecryptor('')
            assert decryptor.decrypt(encrypted_value) == value

    def test_chrome_cookie_decryptor_mac_v10(self):
        with MonkeyPatch(cookies, '_get_mac_keyring_password', lambda *args, **kwargs: '6eIDUdtKAacvlHwBVwvg/Q=='):
            encrypted_value = b'v10\xb3\xbe\xad\xa1[\x9fC\xa1\x98\xe0\x9a\x01\xd9\xcf\xbfc'
            value = '2021-06-01-22'
            decryptor = MacChromeCookieDecryptor('')
            assert decryptor.decrypt(encrypted_value) == value


