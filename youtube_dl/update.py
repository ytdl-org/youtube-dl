from __future__ import unicode_literals

import io
import json
import traceback
import hashlib
import os
import subprocess
import sys
from zipimport import zipimporter

from .compat import (
    compat_str,
    compat_urllib_request,
)
from .utils import make_HTTPS_handler
from .version import __version__


def rsa_verify(message, signature, key):
    from struct import pack
    from hashlib import sha256

    assert isinstance(message, bytes)
    block_size = 0
    n = key[0]
    while n:
        block_size += 1
        n >>= 8
    signature = pow(int(signature, 16), key[1], key[0])
    raw_bytes = []
    while signature:
        raw_bytes.insert(0, pack("B", signature & 0xFF))
        signature >>= 8
    signature = (block_size - len(raw_bytes)) * b'\x00' + b''.join(raw_bytes)
    if signature[0:2] != b'\x00\x01':
        return False
    signature = signature[2:]
    if b'\x00' not in signature:
        return False
    signature = signature[signature.index(b'\x00') + 1:]
    if not signature.startswith(b'\x30\x31\x30\x0D\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20'):
        return False
    signature = signature[19:]
    if signature != sha256(message).digest():
        return False
    return True


def update_self(to_screen, verbose):
    """Update the program file with the latest version from the repository"""

    UPDATE_URL = "https://rg3.github.io/youtube-dl/update/"
    VERSION_URL = UPDATE_URL + 'LATEST_VERSION'
    JSON_URL = UPDATE_URL + 'versions.json'
    UPDATES_RSA_KEY = (0x9d60ee4d8f805312fdb15a62f87b95bd66177b91df176765d13514a0f1754bcd2057295c5b6f1d35daa6742c3ffc9a82d3e118861c207995a8031e151d863c9927e304576bc80692bc8e094896fcf11b66f3e29e04e3a71e9a11558558acea1840aec37fc396fb6b65dc81a1c4144e03bd1c011de62e3f1357b327d08426fe93, 65537)

    if not isinstance(globals().get('__loader__'), zipimporter) and not hasattr(sys, "frozen"):
        to_screen('It looks like you installed youtube-dl with a package manager, pip, setup.py or a tarball. Please use that to update.')
        return

    https_handler = make_HTTPS_handler({})
    opener = compat_urllib_request.build_opener(https_handler)

    # Check if there is a new version
    try:
        newversion = opener.open(VERSION_URL).read().decode('utf-8').strip()
    except Exception:
        if verbose:
            to_screen(compat_str(traceback.format_exc()))
        to_screen('ERROR: can\'t find the current version. Please try again later.')
        return
    if newversion == __version__:
        to_screen('youtube-dl is up-to-date (' + __version__ + ')')
        return

    # Download and check versions info
    try:
        versions_info = opener.open(JSON_URL).read().decode('utf-8')
        versions_info = json.loads(versions_info)
    except Exception:
        if verbose:
            to_screen(compat_str(traceback.format_exc()))
        to_screen('ERROR: can\'t obtain versions info. Please try again later.')
        return
    if 'signature' not in versions_info:
        to_screen('ERROR: the versions file is not signed or corrupted. Aborting.')
        return
    signature = versions_info['signature']
    del versions_info['signature']
    if not rsa_verify(json.dumps(versions_info, sort_keys=True).encode('utf-8'), signature, UPDATES_RSA_KEY):
        to_screen('ERROR: the versions file signature is invalid. Aborting.')
        return

    version_id = versions_info['latest']

    def version_tuple(version_str):
        return tuple(map(int, version_str.split('.')))
    if version_tuple(__version__) >= version_tuple(version_id):
        to_screen('youtube-dl is up to date (%s)' % __version__)
        return

    to_screen('Updating to version ' + version_id + ' ...')
    version = versions_info['versions'][version_id]

    print_notes(to_screen, versions_info['versions'])

    filename = sys.argv[0]
    # Py2EXE: Filename could be different
    if hasattr(sys, "frozen") and not os.path.isfile(filename):
        if os.path.isfile(filename + '.exe'):
            filename += '.exe'

    if not os.access(filename, os.W_OK):
        to_screen('ERROR: no write permissions on %s' % filename)
        return

    # Py2EXE
    if hasattr(sys, "frozen"):
        exe = os.path.abspath(filename)
        directory = os.path.dirname(exe)
        if not os.access(directory, os.W_OK):
            to_screen('ERROR: no write permissions on %s' % directory)
            return

        try:
            urlh = opener.open(version['exe'][0])
            newcontent = urlh.read()
            urlh.close()
        except (IOError, OSError):
            if verbose:
                to_screen(compat_str(traceback.format_exc()))
            to_screen('ERROR: unable to download latest version')
            return

        newcontent_hash = hashlib.sha256(newcontent).hexdigest()
        if newcontent_hash != version['exe'][1]:
            to_screen('ERROR: the downloaded file hash does not match. Aborting.')
            return

        try:
            with open(exe + '.new', 'wb') as outf:
                outf.write(newcontent)
        except (IOError, OSError):
            if verbose:
                to_screen(compat_str(traceback.format_exc()))
            to_screen('ERROR: unable to write the new version')
            return

        try:
            bat = os.path.join(directory, 'youtube-dl-updater.bat')
            with io.open(bat, 'w') as batfile:
                batfile.write('''
@echo off
echo Waiting for file handle to be closed ...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "%s.new" "%s" > NUL
echo Updated youtube-dl to version %s.
start /b "" cmd /c del "%%~f0"&exit /b"
                \n''' % (exe, exe, version_id))

            subprocess.Popen([bat])  # Continues to run in the background
            return  # Do not show premature success messages
        except (IOError, OSError):
            if verbose:
                to_screen(compat_str(traceback.format_exc()))
            to_screen('ERROR: unable to overwrite current version')
            return

    # Zip unix package
    elif isinstance(globals().get('__loader__'), zipimporter):
        try:
            urlh = opener.open(version['bin'][0])
            newcontent = urlh.read()
            urlh.close()
        except (IOError, OSError):
            if verbose:
                to_screen(compat_str(traceback.format_exc()))
            to_screen('ERROR: unable to download latest version')
            return

        newcontent_hash = hashlib.sha256(newcontent).hexdigest()
        if newcontent_hash != version['bin'][1]:
            to_screen('ERROR: the downloaded file hash does not match. Aborting.')
            return

        try:
            with open(filename, 'wb') as outf:
                outf.write(newcontent)
        except (IOError, OSError):
            if verbose:
                to_screen(compat_str(traceback.format_exc()))
            to_screen('ERROR: unable to overwrite current version')
            return

    to_screen('Updated youtube-dl. Restart youtube-dl to use the new version.')


def get_notes(versions, fromVersion):
    notes = []
    for v, vdata in sorted(versions.items()):
        if v > fromVersion:
            notes.extend(vdata.get('notes', []))
    return notes


def print_notes(to_screen, versions, fromVersion=__version__):
    notes = get_notes(versions, fromVersion)
    if notes:
        to_screen('PLEASE NOTE:')
        for note in notes:
            to_screen(note)
