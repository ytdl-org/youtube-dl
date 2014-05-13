
import io
import os.path
import sys
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_FILE = os.path.join(ROOT_DIR, 'README.md')

with io.open(README_FILE, encoding='utf-8') as f:
    readme = f.read()

PREFIX = '%YOUTUBE-DL(1)\n\n# NAME\n'
readme = re.sub(r'(?s)# INSTALLATION.*?(?=# DESCRIPTION)', '', readme)
readme = PREFIX + readme

if sys.version_info < (3, 0):
    print(readme.encode('utf-8'))
else:
    print(readme)
