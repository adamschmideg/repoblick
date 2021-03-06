"""
Store repodata in an sqlite database
"""
import os
import sqlite3

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick import HostInfo
from utils import Timer, file_size, mkdirs, relative_file

class SqliteStore:

    def __init__(self, db_dir):
        mkdirs(db_dir)
        self.path = os.path.join(db_dir, 'logdata.sqlite')
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        self.cursor = con.cursor()
        create_script = relative_file(__file__, 'create.sql')
        with open(create_script) as script:
            self.cursor.executescript(script.read())
        for host_info in [
            HostInfo(shortname='bb', name='bitbucket',
                urnpattern='https://bitbucket.org', vcs='hg',
                lister_module='repoblick.lister.bitbucket'),
            HostInfo(shortname='gh', name='github', urnpattern='https://github.com/%s.git', vcs='git'),
            HostInfo(shortname='gc-hg', name='googlecode-mercurial', urnpattern='https://%s.googlecode.com/hg/', vcs='hg'),
            HostInfo(shortname='gc-svn', name='googlecode-subversion', urnpattern='http://%s.googlecode.com/svn/trunk/', vcs='svn'),
            ]:
            self.add_host(host_info)
        self.commit()
            
    def add_host(self, host_info):
        try:
            self.cursor.execute('''
                insert into hosts (name, urnpattern, shortname, lister_module, vcs)
                values(:name, :urnpattern, :shortname, :lister_module, :vcs)
                ''', host_info.__dict__)
            return self.cursor.lastrowid, True
        except sqlite3.IntegrityError:
            hostid = self.cursor.execute('''
                select id from hosts where name=:name and urnpattern=:urnpattern
                ''', host_info.__dict__).fetchone()[0]
            return hostid, False

    def add_project(self, hostid, name, attrs=None):
        try:
            self.cursor.execute('''
                insert into projects (hostid, name)
                values(?, ?)''',
                (hostid, name))
            projectid = self.cursor.lastrowid
            if attrs:
                for k, v in attrs.items():
                    self.cursor.execute('''
                    insert into projectattrs (projectid, key, value)
                    values(?, ?, ?)''',
                    (projectid, k, v))
            return projectid, True
        except sqlite3.IntegrityError:
            projectid = self.cursor.execute('select id from projects where hostid=? and name=?',
                (hostid, name)).fetchone()[0]
            return projectid, False

    def add_commit(self, projectid, commit):
        try:
            self.cursor.execute('''
                insert into commits(author, date, hash, projectid)
                values(:author, :date, :hash, :projectid)''',
                dict(commit.__dict__, projectid=projectid))
            return self.cursor.lastrowid, True
        except sqlite3.IntegrityError:
            commitid = self.cursor.execute('select id from commits where projectid=? and hash=?',
                (projectid, commit.hash)).fetchone()[0]
            return commitid, False

    def add_file_change(self, commitid, file_change):
        try:
            self.cursor.execute('''
                insert into files(file, commitid, changetype, added, deleted, isbinary)
                values(:filename, :commitid, :change_type, :added_lines, :deleted_lines, :is_binary)''',
                dict(file_change.__dict__, commitid=commitid))
            return self.cursor.lastrowid, True
        except sqlite3.IntegrityError:
            filechangeid = self.cursor.execute('select id from files where commitid=? and file=?',
                (commitid, file_change.filename)).fetchone()[0]
            return filechangeid, False
        
    def get_projects(self, host_info):
        "Get a generator of projects at a host"
        self.cursor.execute('select * from projects where hostid=?',
            [host_info.id])
        return self.cursor
        
    def import_log(self, projectid, mirror):
        "Import logs of a repo_mirror into this store"
        with Timer('Import %s' % mirror.remote_repo):
            try:
                for commit in mirror.commits():
                    commitid, _ = self.add_commit(projectid, commit)
                    for file_change in mirror.changes(commit):
                        self.add_file_change(commitid, file_change)
                self.cursor.connection.commit()
            except:
                self.cursor.connection.rollback()
                print 'Failed to import', mirror
                raise
        print 'Storage used:\t%s' % file_size(self.path)

    def commit(self):
        self.cursor.connection.commit()
