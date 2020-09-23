from __future__ import unicode_literals
from datetime import datetime
# import urllib.request

# response = urllib.request.urlopen('https://blackjack4494.github.io/youtube-dlc/update/LATEST_VERSION')
# _LATEST_VERSION = response.read().decode('utf-8')

exec(compile(open('youtube_dlc/version.py').read(), 'youtube_dlc/version.py', 'exec'))

_LATEST_VERSION = locals()['__version__']

_OLD_VERSION = _LATEST_VERSION.rsplit("-", 1)

if len(_OLD_VERSION) > 0:
    old_ver = _OLD_VERSION[0]

old_rev = ''
if len(_OLD_VERSION) > 1:
    old_rev = _OLD_VERSION[1]

now = datetime.now()
# ver = f'{datetime.today():%Y.%m.%d}'
ver = now.strftime("%Y.%m.%d")
rev = ''

if old_ver == ver:
    if old_rev:
        rev = int(old_rev) + 1
    else:
        rev = 1

_SEPARATOR = '-'

version = _SEPARATOR.join(filter(None, [ver, str(rev)]))

print('::set-output name=ytdlc_version::' + version)

file_version_py = open('youtube_dlc/version.py', 'rt')
data = file_version_py.read()
data = data.replace(locals()['__version__'], version)
file_version_py.close()
file_version_py = open('youtube_dlc/version.py', 'wt')
file_version_py.write(data)
file_version_py.close()
