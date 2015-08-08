from youtube_dl.extractor import *
import re
import os

def list_non_suitable_extractors(age_limit):
    """
    Return a list of extractors that are suitable for the given age,
    sorted by extractor ID.
    """

    return sorted(
        filter(lambda ie: not ie.is_suitable(age_limit), gen_extractors()),
        key=lambda ie: ie.IE_NAME.lower())

non_suitable_extractors = list_non_suitable_extractors(0)

extractors_dir = 'youtube_dl/extractor/'

with open(extractors_dir + '__init__.py') as f:
    content = f.read()
    for extractor in non_suitable_extractors:
        content = re.sub(r'from \.' + extractor.__module__.split('.')[-1] + r' import (?:[A-Za-z0-9,\s]+|\([^\)]+\))\n', '', content)

with open(extractors_dir + '__init__.py', 'w') as f:
    f.write(content)

with open(extractors_dir + 'generic.py') as f:
    content = f.read()
    for extractor in non_suitable_extractors:
        content = re.sub(r'from \.' + extractor.__module__.split('.')[-1] + r' import (?:[A-Za-z0-9,\s]+|\([^\)]+\))\n', '', content)
        content = re.sub(r'#[^#]+' + extractor.__module__.split('.')[-1] + r'[^#]+', '', content)

with open(extractors_dir + 'generic.py', 'w') as f:
    f.write(content)

for extractor in non_suitable_extractors:
    extractor_filename = extractors_dir + extractor.__module__.split('.')[-1] + '.py'
    if os.path.isfile(extractor_filename):
        os.remove(extractor_filename)
