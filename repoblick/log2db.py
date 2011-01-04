from datetime import datetime, timedelta
from optparse import OptionParser
from mercurial import hg, patch, ui, util
from subprocess import Popen, PIPE
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick.store import SqliteStore
from repoblick.utils import Timer
from repoblick import repolist

ADD = 'A'
MOD = 'M'
DEL = 'D'

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


def mirror_repo(remote_url, local_path, max_commits=None):
    """Mirror a remote hg repository to a local clone.  If max_commits is
    not given, all commits are cloned"""
    devnull = open(os.devnull, 'w')
    if os.path.exists(local_path):
        if max_commits:
            proc = Popen(['hg', 'pull', '-r', str(max_commits - 1), '-R', local_path], stdout=devnull)
        else:
            proc = Popen(['hg', 'pull', '-R', local_path], stdout=devnull)
    else:
        os.makedirs(local_path)
        if max_commits:
            proc = Popen(['hg', 'clone', '-r', str(max_commits - 1), remote_url, local_path], stdout=devnull)
        else:
            proc = Popen(['hg', 'clone', remote_url, local_path], stdout=devnull)
    proc.wait()
    devnull.close()


def log2db(store_or_path, host, project, commits=2, working_dir='mirror'):
    """Make log-related entries in the database for a single project"""
    lister = repolist.get_lister(host)
    store = SqliteStore(store_or_path) if type(store_or_path) == str else store_or_path
    hostid, _ = store.add_host(lister.name, lister.urn_pattern)
    projectid, _ = store.add_project(hostid, project)
    remote_repo = lister.urn_pattern % project
    local_repo = remote_repo if lister.is_local() else os.path.join(working_dir, project)
    mirror = HgMirror(remote_repo, local_repo)
    mirror.mirror(commits)
    store.import_log(projectid, mirror)

def repos2db(store_or_path, commits=2, working_dir='mirror'):
    """Read repos from database and put their logs back into the same
    database.  Remote repos are cloned into working_dir."""
    store = SqliteStore(store_or_path) if type(store_or_path) == str else store_or_path
    with Timer('repos2db for %s' % store_or_path):
        for prj in store.get_active_projects():
            project = prj['project']
            remote_repo = prj['urn_pattern'] % project
            if remote_repo.startswith('http://') or remote_repo.startswith('https://') or remote_repo.startswith('ssh://'):
                local_repo = os.path.join(working_dir, project)
            else:
                local_repo = remote_repo
            mirror = HgMirror(remote_repo, local_repo)
            mirror.mirror(commits)
            store.import_log(prj['projectid'], mirror)

def main():
    parser = OptionParser(usage='usage: %prog [options] <dbpath>')
    parser.add_option('-t', '--host', dest='host')
    parser.add_option('-p', '--project', dest='project')
    parser.add_option('-c', '--commits', dest='commit_count', default=2)
    parser.add_option('-m', '--mirror', dest='working_dir', default=2)
    (options, args) = parser.parse_args()
    if (len(args) < 1):
        print 'Missing arguments.  Use --help for details'
    else:
        db_path = args[0]
        if options.host and options.project:
            log2db(db_path, options.host, options.project,
                options.commit_count, options.working_dir)
        elif not options.host and not options.project:
            repos2db(db_path, options.working_dir)
        else:
            print 'Give either both host and project, or none of them'


if __name__ == '__main__':
    main()
