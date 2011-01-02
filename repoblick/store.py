"""
Store repodata in a persistent format, like a database or csv files
"""
import os, sqlite3, time
import sys

from utils import Timer, file_size, relative_file

class SqliteStore:

    def __init__(self, path):
        self.path = path
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        self.cursor = con.cursor()
        create_script = relative_file(__file__, 'create.sql')
        with open(create_script) as script:
            self.cursor.executescript(script.read())
            
    def add_host(self, host_name, urn_pattern):
        try:
            self.cursor.execute('''
                insert into hosts (name, urnpattern)
                values(?, ?)''',
                (host_name, urn_pattern))
            return self.cursor.lastrowid, True
        except sqlite3.IntegrityError:
            id = self.cursor.execute('select id from hosts where name=? and urnpattern=?', 
                (host_name, urn_pattern)).fetchone()[0]
            return id, False

    def add_project(self, hostid, name, attrs=None):
        try:
            self.cursor.execute('''
                insert into projects (hostid, name)
                values(?, ?)''',
                (hostid, name))
            id = self.cursor.lastrowid
            if attrs:
                for k, v in attrs.items():
                    self.cursor.execute('''
                    insert into projectattrs (projectid, key, value)
                    values(?, ?, ?)''',
                    (id, k, v))
            return id, True
        except sqlite3.IntegrityError:
            id = self.cursor.execute('select id from projects where hostid=? and name=?',
                (hostid, name)).fetchone()[0]
            return id, False

    def add_commit(self, projectid, commit):
        try:
            self.cursor.execute('''
                insert into commits(author, date, hash, projectid)
                values(:author, :date, :hash, :projectid)''',
                dict(commit.__dict__, projectid=projectid))
            return self.cursor.lastrowid, True
        except sqlite3.IntegrityError:
            id = self.cursor.execute('select id from commits where projectid=? and hash=?',
                (projectid, commit.hash)).fetchone()[0]
            return id, False

    def add_file_change(self, commitid, file_change):
        try:
            self.cursor.execute('''
                insert into files(file, commitid, changetype, added, deleted, isbinary)
                values(:filename, :commitid, :change_type, :added_lines, :deleted_lines, :is_binary)''',
                dict(file_change.__dict__, commitid=commitid))
            return self.cursor.lastrowid, True
        except sqlite3.IntegrityError:
            id = self.cursor.execute('select id from files where commitid=? and file=?',
                (commitid, file_change.filename)).fetchone()[0]
            return id, False
        
    def get_active_projects(self):
        return self.cursor.execute('''
            select h.urnpattern, p.name as project, p.id as projectid
            from hosts h, projects p
            where p.status is null''').fetchall()
        
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
