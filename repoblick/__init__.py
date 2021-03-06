import os

ADD = 'A'
MOD = 'M'
DEL = 'D'

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

    def project_remote_url(self, project):
        "Get the full url of a project using the urnpattern"
        if '%s' in self.urnpattern:
            return self.urnpattern % project
        elif self.urnpattern.endswith('/'):
            return self.urnpattern + project
        else:
            return self.urnpattern + '/' + project

    def project_local_path(self, working_dir, project):
        "Get the local path for a project"
        return os.path.join(working_dir, 'mirror', self.name, project)

class Commit:
    "Info for one changeset"
    def __init__(self, hash_, date, author, message, file_changes):
        self.hash = hash_
        self.date = date
        self.author = unicode(author, errors='replace')
        self.message = unicode(message, errors='replace')
        self.file_changes = file_changes

    def __unicode__(self):
        return unicode(self.__dict__)


class FileChange:
    "Info about how a file was changed"
    def __init__(self, filename, change_type, added_lines, deleted_lines, is_binary):
        self.filename = unicode(filename, errors='replace')
        self.change_type = change_type
        self.added_lines = added_lines
        self.deleted_lines = deleted_lines
        self.is_binary = is_binary
