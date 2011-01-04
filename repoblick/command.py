from datetime import datetime, timedelta
from subprocess import Popen, PIPE
import os

from mercurial import hg, patch, ui, util

from repoblick.log2db import Commit, FileChange, ADD, MOD, DEL

def _file_split(line):
    "Split a file list at semi-colons"
    if line:
        return line.split(';')
    else:
        return ()

def commits(local_repo_path):
    """Return Commit instances"""
    dir_ = os.path.dirname(__file__)
    style = os.path.join(dir_, '..', 'hg/style')
    proc = Popen(['hg', 'log', '-R', local_repo_path, '--style', style], stdout=PIPE)
    for line in proc.stdout.readlines():
        line = line.rstrip()
        hash_, date, author, message, files_add, files_mod, files_del = line.split('|')
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

def file_changes(hg_ui, local_repo_path, commit):
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
        for commit in commits(local_repo_path):
            commitid, _ = store.add_commit(projectid, commit)
            for file_change in file_changes(hg_ui, local_repo_path, commit):
                store.add_file_change(commitid, file_change)
        store.cursor.connection.commit()
    except:
        store.cursor.connection.rollback()
        print 'Warn: Failed to import %s' % local_repo_path
        raise
