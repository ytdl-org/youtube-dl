from __future__ import unicode_literals


class Params(dict):
    """Params class

    The params class holds the parameters for YoutubeDL objects, in its
    simplest form it's initialized with a dictionary with the parameters. To
    override some parameter in an info extractor a dictionary can be passed as
    the second argument, its keys must match the IE_NAME properties of the
    extractors.
    """
    def __init__(self, params, sections=None):
        super(Params, self).__init__(params)
        if sections is None:
            sections = {}
        self.sections = sections

    def section(self, section):
        """Return the params for the specified section"""
        return ParamsSection(self.sections.get(section, {}), self)


class ParamsSection(object):
    def __init__(self, main=None, parent=None):
        if main is None:
            main = {}
        if parent is None:
            parent = Params({})
        self.main = main
        self.parent = parent

    def __getitem__(self, key):
        if key in self.main:
            return self.main[key]
        else:
            return self.parent[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def sections(self):
        return self.parent.sections

    def section(self, section):
        return ParamsSection(self.parent.sections.get(section, {}), self)
