# Legacy file for backwards compatibility, use youtube_dl.extractor instead!

from .extractor.common import InfoExtractor, SearchInfoExtractor
from .extractor import gen_extractors, get_info_extractor
