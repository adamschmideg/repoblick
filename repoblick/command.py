from datetime import datetime, timedelta
from subprocess import Popen, PIPE
import os

from mercurial import hg, patch, ui, util

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick import Commit, FileChange, HostInfo, ADD, MOD, DEL
from repoblick.store import SqliteStore
from repoblick.utils import Timer, make_int

def _split_unknown_host(host):
    """Split a host not found in db to (host_info, project)
    >>> info, prj = _split_unknown_host('http://example.com/foo/bar')
    >>> prj
    'foo/bar'
    >>> info.name
    'http/example-com'
    >>> info.urnpattern
    'http://example.com'
    >>> info, prj = _split_unknown_host('http://repo.example.com')
    >>> prj
    >>> info.name
    'http/repo-example-com'
    >>> info, prj = _split_unknown_host('/path/to/somewhere')
    >>> prj
    >>> info.name
    'local/path-to-somewhere'
    """
    # It may start with a protocol
    try:
        proto, rest = host.split('://')
        try:
            host_name, project = rest.split('/', 1)
        except ValueError:
            host_name = rest
            project = None
        name = '%s/%s' % (proto,
            host_name.replace('/', '-').replace('.', '-'))
        urnpattern = '%s://%s' % (proto, host_name)
        host_info = HostInfo(name=name, urnpattern=urnpattern)
    except ValueError:
        # It must be a local path
        name = os.path.abspath(host).replace(os.path.sep, '-')
        if name.startswith('-'):
            name = name[1:]
        name = 'local/%s' % name
        project = None
        host_info = HostInfo(name=name, urnpattern=host,
            lister_module='repoblick.lister.local')
    # Make a host_info
    return host_info, project

def _split_host(store, host):
    """Split a host name to (host_info, project) where project may
    be None if the whole name can be recognized as a host.  The
    host_info is guaranteed to be saved in store.
    >>> import tempfile, shutil
    >>> db_dir = tempfile.mkdtemp()
    >>> store = SqliteStore(db_dir)
    >>> info, prj = _split_host(store, 'bb')
    >>> prj
    >>> info.name
    u'bitbucket'
    >>> info, prj = _split_host(store, 'https://bitbucket.org/foo/bar')
    >>> prj
    'foo/bar'
    >>> info.name
    u'bitbucket'
    
    Unrecognized hosts are saved
    >>> info, prj = _split_host(store, '/path/to/location')
    >>> new_info, prj = _split_host(store, '/path/to/location')
    >>> info.id == new_info.id
    True
    >>> shutil.rmtree(db_dir)
    """
    # Try an exact match
    store.cursor.execute('''
        select * from hosts where shortname=:host
        union
        select * from hosts where name=:host
        union
        select * from hosts where urnpattern=:host
        ''', dict(host=host))
    raw_info = store.cursor.fetchone()
    if raw_info:
        host_info = HostInfo(**raw_info)
        project = None
    else:
        # Try a partial match with urnpattern
        store.cursor.execute('''
            select * from hosts where :host like urnpattern || "%"
            ''', dict(host=host))
        raw_info = store.cursor.fetchone()
        if raw_info:
            host_info = HostInfo(**raw_info)
            project = host[len(host_info.urnpattern) + 1:]
        else:
            # It's an unknown host yet
            host_info, project = _split_unknown_host(host)
            hostid, _ = store.add_host(host_info)
            store.commit()
            host_info.id = hostid
    return host_info, project

def _file_split(line):
    "Split a file list at semi-colons"
    if line:
        return line.split(';')
    else:
        return ()

def _commits(local_repo_path):
    """Return Commit instances"""
    dir_ = os.path.dirname(__file__)
    style = os.path.join(dir_, '..', 'hg/style')
    proc = Popen(['hg', 'log', '-R', local_repo_path, '--style', style], stdout=PIPE)
    for line in proc.stdout.readlines():
        line = line.rstrip()
        hash_, date, author, files_add, files_mod, files_del, message = line.split('|', 6)
        timestamp, offset = [int(d) for d in date.split(' ')]
        date = datetime.fromtimestamp(timestamp) + timedelta(seconds=offset)
        files = {}
        for f in _file_split(files_add):
            files[f] = ADD
        for f in _file_split(files_mod):
            files[f] = MOD
        for f in _file_split(files_del):
            files[f] = DEL
        yield Commit(hash_, date, author, message, files)

def _file_changes(hg_ui, local_repo_path, commit):
    "Return FileChange instances for a commit"
    repo = hg.repository(hg_ui, path=local_repo_path)
    node2 = repo.lookup(commit.hash)
    node1 = repo[node2].parents()[0].node()
    lines = util.iterlines(patch.diff(repo, node1, node2))
    for f in patch.diffstatdata(lines):
        yield FileChange(f[0], commit.file_changes[f[0]], f[1], f[2], f[3])

def import_log(store, projectid, local_repo_path):
    """Import log data from local_repo_path into store"""
    try:
        hg_ui = ui.ui()
        for commit in _commits(local_repo_path):
            commitid, commit_saved = store.add_commit(projectid, commit)
            if not commit_saved:
                for file_change in _file_changes(hg_ui, local_repo_path, commit):
                    store.add_file_change(commitid, file_change)
        store.cursor.connection.commit()
    except:
        store.cursor.connection.rollback()
        print 'Warn: Failed to import %s' % local_repo_path
        raise

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


if __name__ == '__main__':
   import doctest
   doctest.testmod()
