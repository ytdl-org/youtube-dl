"""
test_fork.py is not added to git (only for local testing)
"""

from __future__ import unicode_literals
import youtube_dl

ydl_opts = {
    'skip_download': True,
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['http://www.pornhub.com/view_video.php?viewkey=1331683002'])

exit()

ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]',
    'username': "tdsist",
    'password': "ZtOUktu0QP",
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://fr.pornhubpremium.com/view_video.php?viewkey=ph5bdbb2cd6df6a'])