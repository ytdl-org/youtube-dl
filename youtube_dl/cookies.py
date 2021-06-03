import ctypes
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import warnings

from youtube_dl.compat import compat_cookiejar_Cookie, compat_b64decode, Compat_TemporaryDirectory, compat_ord
from youtube_dl.utils import YoutubeDLCookieJar, expand_path

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA1
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


SUPPORTED_BROWSERS = ['firefox', 'chrome', 'chrome_beta', 'chrome_dev', 'chromium', 'brave', 'opera',
                      'edge', 'edge_beta']


class Logger:
    def info(self, message):
        print(message)

    def error(self, message):
        print(message, file=sys.stderr)


def extract_cookies_from_browser(browser_name, logger=Logger()):
    if browser_name == 'firefox':
        return _extract_firefox_cookies(logger)
    elif browser_name in ('chrome', 'chrome_beta', 'chrome_dev', 'chromium',
                          'brave', 'opera', 'edge', 'edge_beta'):
        return _extract_chrome_cookies(browser_name, logger)
    else:
        raise ValueError('unknown browser: {}'.format(browser_name))


def _extract_firefox_cookies(logger):
    logger.info('extracting cookies from firefox')

    if sys.platform in ('linux', 'linux2'):
        root = os.path.expanduser('~/.mozilla/firefox')
    elif sys.platform == 'win32':
        root = os.path.expandvars(r'%APPDATA%\Mozilla\Firefox')
    elif sys.platform == 'darwin':
        root = os.path.expanduser('~/Library/Application Support/Firefox')
    else:
        raise ValueError('unsupported platform: {}'.format(sys.platform))

    cookie_database_path = _find_most_recently_used_file(root, 'cookies.sqlite')
    if cookie_database_path is None:
        raise FileNotFoundError('could not find firefox cookies database')

    with Compat_TemporaryDirectory(prefix='youtube_dl') as tmpdir:
        cursor = None
        try:
            cursor = _open_database_copy(cookie_database_path, tmpdir)
            cursor.execute('SELECT host, name, value, path, expiry, isSecure FROM moz_cookies')
            jar = YoutubeDLCookieJar()
            for host, name, value, path, expiry, is_secure in cursor.fetchall():
                cookie = compat_cookiejar_Cookie(
                    version=0, name=name, value=value, port=None, port_specified=False,
                    domain=host, domain_specified=bool(host), domain_initial_dot=host.startswith('.'),
                    path=path, path_specified=bool(path), secure=is_secure, expires=expiry, discard=False,
                    comment=None, comment_url=None, rest={})
                jar.set_cookie(cookie)
            logger.info('extracted {} cookies from firefox'.format(len(jar)))
            return jar
        finally:
            if cursor is not None:
                cursor.connection.close()


def _get_chrome_like_browser_settings(browser_name):
    # https://chromium.googlesource.com/chromium/src/+/HEAD/docs/user_data_dir.md
    if sys.platform in ('linux', 'linux2'):
        config = _config_home()
        browser_dir = {
            'chrome': os.path.join(config, 'google-chrome'),
            'chrome_beta': os.path.join(config, 'google-chrome-beta'),
            'chrome_dev': os.path.join(config, 'google-chrome-unstable'),
            'chromium': os.path.join(config, 'chromium'),
            'brave': os.path.join(config, 'BraveSoftware/Brave-Browser'),
            'opera': os.path.join(config, 'opera'),
            'edge': os.path.join(config, 'microsoft-edge'),
            'edge_beta': os.path.join(config, 'microsoft-edge-beta'),
        }[browser_name]

    elif sys.platform == 'win32':
        appdata_local = os.path.expandvars('%LOCALAPPDATA%')
        appdata_roaming = os.path.expandvars('%APPDATA%')
        browser_dir = {
            'chrome': os.path.join(appdata_local, r'Google\Chrome'),
            'chrome_beta': os.path.join(appdata_local, r'Google\Chrome Beta'),
            'chrome_dev': os.path.join(appdata_local, r'Google\Chrome SxS'),
            'chromium': os.path.join(appdata_local, r'Google\Chromium'),
            'brave': os.path.join(appdata_local, r'BraveSoftware\Brave-Browser'),
            'opera': os.path.join(appdata_roaming, r'Opera Software\Opera Stable'),
            'edge': os.path.join(appdata_local, r'Microsoft\Edge'),
            'edge_beta': os.path.join(appdata_local, r'Microsoft\Edge Beta'),
        }[browser_name]

    elif sys.platform == 'darwin':
        appdata = os.path.expanduser('~/Library/Application Support')
        browser_dir = {
            'chrome': os.path.join(appdata, 'Google/Chrome'),
            'chrome_beta': os.path.join(appdata, 'Google/Chrome Beta'),
            'chrome_dev': os.path.join(appdata, 'Google/Chrome Canary'),
            'chromium': os.path.join(appdata, 'Google/Chromium'),
            'brave': os.path.join(appdata, 'BraveSoftware/Brave-Browser'),
            'opera': os.path.join(appdata, 'com.operasoftware.Opera'),
            'edge': os.path.join(appdata, 'Microsoft Edge'),
        }[browser_name]

    else:
        raise ValueError('unsupported platform: {}'.format(sys.platform))

    keyring_name = {
        'chrome': 'Chrome',
        'chrome_beta': 'Chrome',
        'chrome_dev': 'Chrome',
        'chromium': 'Chromium',
        'brave': 'Brave',
        'opera': 'Opera' if sys.platform == 'darwin' else 'Chromium',
        'edge': 'Mirosoft Edge' if sys.platform == 'darwin' else 'Chromium',
        'edge_beta': 'Mirosoft Edge' if sys.platform == 'darwin' else 'Chromium',
    }[browser_name]

    return {
        'browser_dir': browser_dir,
        'keyring_name': keyring_name
    }


def _extract_chrome_cookies(browser_name, logger):
    logger.info('extracting cookies from {}'.format(browser_name))
    config = _get_chrome_like_browser_settings(browser_name)

    cookie_database_path = _find_most_recently_used_file(config['browser_dir'], 'Cookies')
    if cookie_database_path is None:
        raise FileNotFoundError('could not find {} cookies database'.format(browser_name))

    decryptor = get_cookie_decryptor(config['browser_dir'], config['keyring_name'], logger)

    with Compat_TemporaryDirectory(prefix='youtube_dl') as tmpdir:
        cursor = None
        try:
            cursor = _open_database_copy(cookie_database_path, tmpdir)
            cursor.connection.text_factory = bytes
            cursor.execute('SELECT host_key, name, value, encrypted_value, path, expires_utc, is_secure FROM cookies')
            jar = YoutubeDLCookieJar()
            failed_cookies = 0
            for host_key, name, value, encrypted_value, path, expires_utc, is_secure in cursor.fetchall():
                host_key = host_key.decode('utf-8')
                name = name.decode('utf-8')
                value = value.decode('utf-8')
                path = path.decode('utf-8')

                if not value and encrypted_value:
                    value = decryptor.decrypt(encrypted_value)
                    if value is None:
                        failed_cookies += 1
                        continue

                cookie = compat_cookiejar_Cookie(
                    version=0, name=name, value=value, port=None, port_specified=False,
                    domain=host_key, domain_specified=bool(host_key), domain_initial_dot=host_key.startswith('.'),
                    path=path, path_specified=bool(path), secure=is_secure, expires=expires_utc, discard=False,
                    comment=None, comment_url=None, rest={})
                jar.set_cookie(cookie)
            if failed_cookies > 0:
                failed_message = ' ({} could not be decrypted)'.format(failed_cookies)
            else:
                failed_message = ''
            logger.info('extracted {} cookies from {}{}'.format(len(jar), browser_name, failed_message))
            return jar
        finally:
            if cursor is not None:
                cursor.connection.close()


class ChromeCookieDecryptor:
    """
    Overview:

        Linux:
        - cookies are either v10 or v11
            - v10: AES-CBC encrypted with a fixed key
            - v11: AES-CBC encrypted with an OS protected key (keyring)
            - v11 keys can be stored in various places depending on the activate desktop environment [2]

        Mac:
        - cookies are either v10 or not v10
            - v10: AES-CBC encrypted with an OS protected key (keyring) and more key derivation iterations than linux
            - not v10: 'old data' stored as plaintext

        Windows:
        - cookies are either v10 or not v10
            - v10: AES-GCM encrypted with a key which is encrypted with DPAPI
            - not v10: encrypted with DPAPI

    Sources:
    - [1] https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/
    - [2] https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/key_storage_linux.cc
        - KeyStorageLinux::CreateService
    """

    def decrypt(self, encrypted_value):
        raise NotImplementedError


def get_cookie_decryptor(browser_root, browser_keyring_name, logger):
    if sys.platform in ('linux', 'linux2'):
        return LinuxChromeCookieDecryptor(browser_keyring_name)
    elif sys.platform == 'darwin':
        return MacChromeCookieDecryptor(browser_keyring_name)
    elif sys.platform == 'win32':
        return WindowsChromeCookieDecryptor(browser_root, logger)
    else:
        raise NotImplementedError('Chrome cookie decryption is not supported '
                                  'on this platform: {}'.format(sys.platform))


class LinuxChromeCookieDecryptor(ChromeCookieDecryptor):
    def __init__(self, browser_keyring_name):
        self._v10_key = None
        self._v11_key = None
        if CRYPTO_AVAILABLE:
            self._v10_key = self.derive_key('peanuts')
            if KEYRING_AVAILABLE:
                self._v11_key = self.derive_key(_get_linux_keyring_password(browser_keyring_name))

    @staticmethod
    def derive_key(password):
        # values from
        # https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/os_crypt_linux.cc
        return PBKDF2(password, salt=b'saltysalt', dkLen=16, count=1, hmac_hash_module=SHA1)

    def decrypt(self, encrypted_value):
        version = encrypted_value[:3]
        ciphertext = encrypted_value[3:]

        if version == b'v10':
            if self._v10_key is None:
                warnings.warn('cannot decrypt cookie as the module `pycryptodome` is not installed')
                return None
            return _decrypt_aes_cbc(ciphertext, self._v10_key)

        elif version == b'v11':
            if self._v11_key is None:
                warnings.warn('cannot decrypt cookie as the `pycryptodome` or `keyring` modules are not installed')
                return None
            return _decrypt_aes_cbc(ciphertext, self._v11_key)

        else:
            return None


class MacChromeCookieDecryptor(ChromeCookieDecryptor):
    def __init__(self, browser_keyring_name):
        self._v10_key = None
        if CRYPTO_AVAILABLE:
            self._v10_key = self.derive_key(_get_mac_keyring_password(browser_keyring_name))

    @staticmethod
    def derive_key(password):
        # values from
        # https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/os_crypt_mac.mm
        return PBKDF2(password, salt=b'saltysalt', dkLen=16, count=1003, hmac_hash_module=SHA1)

    def decrypt(self, encrypted_value):
        version = encrypted_value[:3]
        ciphertext = encrypted_value[3:]

        if version == b'v10':
            if self._v10_key is None:
                warnings.warn('cannot decrypt cookie as the `pycryptodome` module is not installed')
                return None
            return _decrypt_aes_cbc(ciphertext, self._v10_key)

        else:
            # other prefixes are considered 'old data' which were stored as plaintext
            # https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/os_crypt_mac.mm
            return encrypted_value


class WindowsChromeCookieDecryptor(ChromeCookieDecryptor):
    def __init__(self, browser_root, logger):
        self._logger = logger
        self._v10_key = _get_windows_v10_password(browser_root, logger)

    def decrypt(self, encrypted_value):
        version = encrypted_value[:3]
        ciphertext = encrypted_value[3:]

        if version == b'v10':
            if self._v10_key is None:
                warnings.warn('cannot decrypt cookie')
                return None

            # https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/os_crypt_win.cc
            #   kNonceLength
            nonce_length = 96 // 8
            # boringssl
            #   EVP_AEAD_AES_GCM_TAG_LEN
            authentication_tag_length = 16

            raw_ciphertext = ciphertext
            nonce = raw_ciphertext[:nonce_length]
            ciphertext = raw_ciphertext[nonce_length:-authentication_tag_length]
            authentication_tag = raw_ciphertext[-authentication_tag_length:]

            return _decrypt_aes_gcm(ciphertext, self._v10_key, nonce, authentication_tag)

        else:
            # any other prefix means the data is DPAPI encrypted
            # https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/os_crypt/os_crypt_win.cc
            return _decrypt_windows_dpapi(encrypted_value, self._logger)


def _get_linux_keyring_password(browser_keyring_name):
    if KEYRING_AVAILABLE:
        password = keyring.get_password('{} Keys'.format(browser_keyring_name),
                                        '{} Safe Storage'.format(browser_keyring_name))
        if password is None:
            # this sometimes occurs in KDE because chrome does not check hasEntry and instead
            # just tries to read the value (which kwallet returns "") whereas keyring checks hasEntry
            # to verify this:
            # dbus-monitor "interface='org.kde.KWallet'" "type=method_return"
            # while starting chrome.
            # this may be a bug as the intended behaviour is to generate a random password and store
            # it, but that doesn't matter here.
            password = ''
        return password


def _get_mac_keyring_password(browser_keyring_name):
    if KEYRING_AVAILABLE:
        return keyring.get_password('{} Safe Storage'.format(browser_keyring_name), browser_keyring_name)
    else:
        proc = subprocess.Popen(['security', 'find-generic-password',
                                 '-w',  # write password to stdout
                                 '-a', browser_keyring_name,  # match 'account'
                                 '-s', '{} Safe Storage'.format(browser_keyring_name)],  # match 'service'
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
        proc.wait()
        if proc.returncode == 0:
            return proc.stdout.read().decode('utf-8').strip()
        else:
            return None


def _get_windows_v10_password(browser_root, logger):
    path = _find_most_recently_used_file(browser_root, 'Local State')
    if path is None:
        logger.error('could not find local state file')
        return None
    with open(path, 'r') as f:
        data = json.load(f)
    try:
        base64_password = data['os_crypt']['encrypted_key']
    except KeyError:
        logger.error('no encrypted key in Local State')
        return None
    encrypted_password = compat_b64decode(base64_password)
    prefix = b'DPAPI'
    if not encrypted_password.startswith(prefix):
        logger.error('invalid key')
        return None
    return _decrypt_windows_dpapi(encrypted_password[len(prefix):], logger)


def _decrypt_aes_cbc(ciphertext, key, initialization_vector=b' ' * 16):
    cipher = AES.new(key, AES.MODE_CBC, iv=initialization_vector)
    plaintext = cipher.decrypt(ciphertext)
    padding_length = compat_ord(plaintext[-1])
    try:
        return plaintext[:-padding_length].decode('utf-8')
    except UnicodeDecodeError:
        warnings.warn('failed to decrypt cookie because UTF-8 decoding failed. Possibly the key is wrong?')
        return None


def _decrypt_aes_gcm(ciphertext, key, nonce, authentication_tag):
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, authentication_tag)
    except ValueError:
        warnings.warn('failed to decrypt cookie because the MAC check failed. Possibly the key is wrong?')
        return None

    try:
        return plaintext.decode('utf-8')
    except UnicodeDecodeError:
        warnings.warn('failed to decrypt cookie because UTF-8 decoding failed. Possibly the key is wrong?')
        return None


def _decrypt_windows_dpapi(ciphertext, logger):
    """
    References:
        - https://docs.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptunprotectdata
    """
    from ctypes.wintypes import DWORD

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', DWORD),
                    ('pbData', ctypes.POINTER(ctypes.c_char))]

    buffer = ctypes.create_string_buffer(ciphertext)
    blob_in = DATA_BLOB(ctypes.sizeof(buffer), buffer)
    blob_out = DATA_BLOB()
    ret = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),  # pDataIn
        None,  # ppszDataDescr: human readable description of pDataIn
        None,  # pOptionalEntropy: salt?
        None,  # pvReserved: must be NULL
        None,  # pPromptStruct: information about prompts to display
        0,  # dwFlags
        ctypes.byref(blob_out)  # pDataOut
    )
    if not ret:
        logger.info('failed to decrypt with DPAPI')
        return None

    result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
    ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    return result


def _config_home():
    return os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))


def _open_database_copy(database_path, tmpdir):
    # cannot open sqlite databases if they are already in use (e.g. by the browser)
    database_copy_path = os.path.join(tmpdir, 'temporary.sqlite')
    shutil.copy(database_path, database_copy_path)
    conn = sqlite3.connect(database_copy_path)
    return conn.cursor()


def _find_most_recently_used_file(root, filename):
    # if there are multiple browser profiles, take the most recently used one
    paths = []
    for root, dirs, files in os.walk(root):
        for file in files:
            if file == filename:
                paths.append(os.path.join(root, file))
    return None if not paths else max(paths, key=lambda path: os.lstat(path).st_mtime)


def _merge_cookie_jars(jars):
    output_jar = YoutubeDLCookieJar()
    for jar in jars:
        for cookie in jar:
            output_jar.set_cookie(cookie)
        if jar.filename is not None:
            output_jar.filename = jar.filename
    return output_jar


class YDLLogger(Logger):
    def __init__(self, ydl):
        self._ydl = ydl

    def info(self, message):
        self._ydl.to_screen(message)

    def error(self, message):
        self._ydl.to_stderr(message)


def load_cookies(cookie_file, browser, ydl):
    cookie_jars = []
    if browser is not None:
        cookie_jars.append(extract_cookies_from_browser(browser, YDLLogger(ydl)))

    if cookie_file is not None:
        cookie_file = expand_path(cookie_file)
        jar = YoutubeDLCookieJar(cookie_file)
        if os.access(cookie_file, os.R_OK):
            jar.load(ignore_discard=True, ignore_expires=True)
        cookie_jars.append(jar)

    return _merge_cookie_jars(cookie_jars)