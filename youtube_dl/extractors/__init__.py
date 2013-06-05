

# Here is where we add new extractors, the order is important.
# You add the IE name without the IE suffix, i.e: for YoutubeIE you add 'Youtube'
extractor_names = ['Test','Test2']


extractor_classes = None

def gen_extractors():
    return [get_info_extractor(name)() for name in extractor_names]

def ie_fullname(IE_name):
    return '%sIE' % IE_name

def get_ieclass_from_module(IE_name):
    full_name = ie_fullname(IE_name)
    module = __import__(full_name,
                        globals(),
                        level = 1 # We want to use the relative import, only needed in Python 3
                        )
    return getattr(module, full_name) # We get the IE class from the module object

def gen_extractor_classes():
    global extractor_classes
    # We save the results for later use, it may save us some time
    if extractor_classes is None:
        # We must keep 2.6 compatibility, so no dict comprehension
        extractor_classes = dict((ie_fullname(name), get_ieclass_from_module(name)) for name in extractor_names)
    return extractor_classes

def get_info_extractor(ie_name):
    """Returns the info extractor class with the given ie_name"""
    return gen_extractor_classes()[ie_name+'IE']
