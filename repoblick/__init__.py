
class HostInfo:
    """Information about a host that is needed to mirror a repo from
    it.  It may include a lister class, too."""
    def __init__(self, name, urnpattern, shortname=None,
            lister_module=None, vcs=None, id=None):
        self.name = name
        self.urnpattern = urnpattern
        self.shortname = shortname
        self.lister_module = lister_module
        self.vcs = vcs
        self.id = id

    def project_url(self, project):
        "Get the full url of a project using the urnpattern"
        if '%s' in self.urnpattern:
            return self.urnpattern % project
        elif self.urnpattern.endswith('/'):
            return self.urnpattern + project
        else:
            return self.urnpattern + '/' + project
