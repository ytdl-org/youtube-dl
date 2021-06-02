import unittest
from unittest import mock

from youtube_dl.cookies import LinuxChromeCookieDecryptor, WindowsChromeCookieDecryptor, CRYPTO_AVAILABLE, \
    MacChromeCookieDecryptor


@unittest.skipIf(not CRYPTO_AVAILABLE, 'cryptography library not available')
class TestCookies(unittest.TestCase):
    @mock.patch('youtube_dl.cookies._get_linux_keyring_password')
    def test_chrome_cookie_decryptor_linux_v10(self, mock_get_keyring_password):
        mock_get_keyring_password.return_value = ''
        encrypted_value = b'v10\xccW%\xcd\xe6\xe6\x9fM" \xa7\xb0\xca\xe4\x07\xd6'
        value = 'USD'
        decryptor = LinuxChromeCookieDecryptor('Chrome')
        assert decryptor.decrypt(encrypted_value) == value

    @mock.patch('youtube_dl.cookies._get_linux_keyring_password')
    def test_chrome_cookie_decryptor_linux_v11(self, mock_get_keyring_password):
        mock_get_keyring_password.return_value = ''
        encrypted_value = b'v11#\x81\x10>`w\x8f)\xc0\xb2\xc1\r\xf4\x1al\xdd\x93\xfd\xf8\xf8N\xf2\xa9\x83\xf1\xe9o\x0elVQd'
        value = 'tz=Europe.London'
        decryptor = LinuxChromeCookieDecryptor('Chrome')
        assert decryptor.decrypt(encrypted_value) == value

    @mock.patch('youtube_dl.cookies._get_windows_v10_password')
    def test_chrome_cookie_decryptor_windows_v10(self, mock_get_windows_v10_password):
        mock_get_windows_v10_password.return_value = b'Y\xef\xad\xad\xeerp\xf0Y\xe6\x9b\x12\xc2<z\x16]\n\xbb\xb8\xcb\xd7\x9bA\xc3\x14e\x99{\xd6\xf4&'
        encrypted_value = b'v10T\xb8\xf3\xb8\x01\xa7TtcV\xfc\x88\xb8\xb8\xef\x05\xb5\xfd\x18\xc90\x009\xab\xb1\x893\x85)\x87\xe1\xa9-\xa3\xad='
        value = '32101439'
        decryptor = WindowsChromeCookieDecryptor('')
        assert decryptor.decrypt(encrypted_value) == value

    @mock.patch('youtube_dl.cookies._get_mac_keyring_password')
    def test_chrome_cookie_decryptor_mac_v10(self, mock_get_keyring_password):
        mock_get_keyring_password.return_value = '6eIDUdtKAacvlHwBVwvg/Q=='
        encrypted_value = b'v10\xb3\xbe\xad\xa1[\x9fC\xa1\x98\xe0\x9a\x01\xd9\xcf\xbfc'
        value = '2021-06-01-22'
        decryptor = MacChromeCookieDecryptor('')
        assert decryptor.decrypt(encrypted_value) == value


