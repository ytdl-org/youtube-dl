#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import tempfile
import urllib.request

URL = 'https://github.com/downloads/rg3/youtube-dl/youtube-dl'

with tempfile.NamedTemporaryFile(suffix='youtube-dl', delete=True) as ytdl_file:
    with urllib.request.urlopen(URL) as dl:
        shutil.copyfileobj(dl, ytdl_file)

    ytdl_file.seek(0)
    data = ytdl_file.read()

    ytdl_file.flush()
    version = subprocess.check_output(['python3', ytdl_file.name, '--version']).decode('ascii').strip()

# Read template page
with open('download.html.in', 'r', encoding='utf-8') as tmplf:
    template = tmplf.read()

md5sum = hashlib.md5(data).hexdigest()
sha1sum = hashlib.sha1(data).hexdigest()
sha256sum = hashlib.sha256(data).hexdigest()
template = template.replace('@PROGRAM_VERSION@', version)
template = template.replace('@PROGRAM_URL@', URL)
template = template.replace('@PROGRAM_MD5SUM@', md5sum)
template = template.replace('@PROGRAM_SHA1SUM@', sha1sum)
template = template.replace('@PROGRAM_SHA256SUM@', sha256sum)
with open('download.html', 'w', encoding='utf-8') as dlf:
    dlf.write(template)
