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
    def __init__(self, hash, date, author, message, fileChanges):
        self.hash = hash
        self.date = date
        self.author = unicode(author, errors='replace')
        self.message = unicode(message, errors='replace')
        self.fileChanges = fileChanges

    def __unicode__(self):
        return unicode(self.__dict__)


class FileChange:
    "Info about how a file was changed"
    def __init__(self, filename, changeType, addedLines, deletedLines, isBinary):
        self.filename = unicode(filename, errors='replace')
        self.changeType = changeType
        self.addedLines = addedLines
        self.deletedLines = deletedLines
        self.isBinary = isBinary


class HgMirror:
    "Local mirror of a remote hg repo"

    def __init__(self, remoteRepo, localRepo):
        self.remoteRepo = remoteRepo
        self.localRepo = localRepo
        # for performance reasons
        self.ui = ui.ui()

    def __str__(self):
        return 'HgMirror(remoteRepo=%s, localRepo=%s)' % (self.remoteRepo, self.localRepo)

    def mirror(self, count=2):
        "Mirror count number of commits from remote to local"
        if self.remoteRepo != self.localRepo:
            with Timer('Mirror %s' % self.remoteRepo):
                devnull = open(os.devnull, 'w')
                if os.path.exists(self.localRepo):
                    if count:
                        p = Popen(['hg', 'pull', '-r', str(count - 1), '-R', self.localRepo], stdout=devnull)
                    else:
                        p = Popen(['hg', 'pull', '-R', self.localRepo], stdout=devnull)
                else:
                    os.makedirs(self.localRepo)
                    if count:
                        p = Popen(['hg', 'clone', '-r', str(count - 1), self.remoteRepo, self.localRepo], stdout=devnull)
                    else:
                        p = Popen(['hg', 'clone', self.remoteRepo, self.localRepo], stdout=devnull)
                p.wait()
                devnull.close()

    def commits(self):
        """Return Commit instances"""
        dir = os.path.dirname(__file__)
        style = os.path.join(dir, '..', 'hg/style')
        p = Popen(['hg', 'log', '-R', self.localRepo, '--style', style], stdout=PIPE)
        def fileSplit(line):
            if line:
                return line.split(';')
            else:
                return ()
        for line in p.stdout.readlines():
            line = line.rstrip()
            hash, date, author, message, files_add, files_mod, files_del = line.split('|')
            ts, offset = [int(d) for d in date.split(' ')]
            date = datetime.fromtimestamp(ts) + timedelta(seconds=offset)
            files = {}
            for f in fileSplit(files_add):
                files[f] = ADD
            for f in fileSplit(files_mod):
                files[f] = MOD
            for f in fileSplit(files_del):
                files[f] = DEL
            yield Commit(hash, date, author, message, files)

    def changes(self, commit):
        "Return FileChange instances"
        repo = hg.repository(self.ui, path=self.localRepo)
        node2 = repo.lookup(commit.hash)
        node1 = repo[node2].parents()[0].node()
        lines = util.iterlines(patch.diff(repo, node1, node2))
        for f in patch.diffstatdata(lines):
            yield FileChange(f[0], commit.fileChanges[f[0]], f[1], f[2], f[3])


def log2db(storeOrPath, host, project, commits=2, workingDir='mirror'):
    """Make log-related entries in the database for a single project"""
    lister = repolist.getLister(host)
    store = SqliteStore(storeOrPath) if type(storeOrPath) == str else storeOrPath
    hostid, _ = store.addHost(lister.name, lister.urnPattern)
    projectid, _ = store.addProject(hostid, project)
    remoteRepo = lister.urnPattern % project
    localRepo = remoteRepo if lister.isLocal() else os.path.join(workingDir, project)
    mirror = HgMirror(remoteRepo, localRepo)
    mirror.mirror(commits)
    store.importLog(projectid, mirror)

def repos2db(storeOrPath, commits=2, workingDir='mirror'):
    """Read repos from database and put their logs back into the same
    database.  Remote repos are cloned into workingDir."""
    store = SqliteStore(storeOrPath) if type(storeOrPath) == str else storeOrPath
    with Timer('repos2db for %s' % storeOrPath):
        for prj in store.getActiveProjects():
            project = prj['project']
            remoteRepo = prj['urnPattern'] % project
            if remoteRepo.startswith('http://') or remoteRepo.startswith('https://') or remoteRepo.startswith('ssh://'):
                localRepo = os.path.join(workingDir, project)
            else:
                localRepo = remoteRepo
            mirror = HgMirror(remoteRepo, localRepo)
            mirror.mirror(commits)
            store.importLog(prj['projectid'], mirror)

def main():
    parser = OptionParser(usage='usage: %prog [options] <dbpath>')
    parser.add_option('-t', '--host', dest='host')
    parser.add_option('-p', '--project', dest='project')
    parser.add_option('-c', '--commits', dest='commitCount', default=2)
    parser.add_option('-m', '--mirror', dest='workingDir', default=2)
    (options, args) = parser.parse_args()
    if (len(args) < 1):
        print 'Missing arguments.  Use --help for details'
    else:
        dbPath = args[0]
        if options.host and options.project:
            log2db(dbPath, options.host, options.project,
                options.commitCount, options.workingDir)
        elif not options.host and not options.project:
            repos2db(dbPath, options.workingDir)
        else:
            print 'Give either both host and project, or none of them'


if __name__ == '__main__':
    main()
