"""
Store repodata in a persistent format, like a database or csv files
"""
import os, sqlite3, time
import sys

from utils import Timer, fileSize, relative_file

class SqliteStore:

  def __init__(self, path):
    self.path = path
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    self.cursor = con.cursor()
    create_script = relative_file(__file__, 'create.sql')
    with open(create_script) as script:
      self.cursor.executescript(script.read())
      
  def addHost(self, hostName, urnPattern):
    try:
      self.cursor.execute('''
        insert into hosts (name, urnpattern)
        values(?, ?)''',
        (hostName, urnPattern))
      return self.cursor.lastrowid, True
    except sqlite3.IntegrityError:
      id = self.cursor.execute('select id from hosts where name=? and urnpattern=?', 
        (hostName, urnPattern)).fetchone()[0]
      return id, False

  def addProject(self, hostid, name, attrs=None):
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

  def addCommit(self, projectid, commit):
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

  def addFileChange(self, commitid, fileChange):
    try:
      self.cursor.execute('''
        insert into files(file, commitid, changetype, added, deleted, isbinary)
        values(:filename, :commitid, :changeType, :addedLines, :deletedLines, :isBinary)''',
        dict(fileChange.__dict__, commitid=commitid))
      return self.cursor.lastrowid, True
    except sqlite3.IntegrityError:
      id = self.cursor.execute('select id from files where commitid=? and file=?',
        (commitid, fileChange.filename)).fetchone()[0]
      return id, False
    
  def getActiveProjects(self):
    return self.cursor.execute('''
      select h.urnpattern, p.name as project, p.id as projectid
      from hosts h, projects p
      where p.status is null''').fetchall()
    
  def importLog(self, projectid, mirror):
    "Import logs of a repoMirror into this store"
    with Timer('Import %s' % mirror.remoteRepo):
      try:
        for commit in mirror.commits():
          commitid, _ = self.addCommit(projectid, commit)
          for fileChange in mirror.changes(commit):
            self.addFileChange(commitid, fileChange)
        self.cursor.connection.commit()
      except:
        self.cursor.connection.rollback()
        print 'Failed to import', mirror
        raise
    print 'Storage used:\t%s' % fileSize(self.path)

  def commit(self):
    self.cursor.connection.commit()
