"""
Store repodata in a persistent format, like a database or csv files
"""
import os, sqlite3, time
from utils import Timer, fileSize

class SqliteStore:

  def __init__(self, path):
    self.path = path
    self.cursor = sqlite3.connect(path).cursor()
    createScript = os.path.join(os.path.dirname(__file__), 'create.sql')
    with open(createScript) as script:
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
    
  def importLog(self, mirror):
    "Import logs of a repoMirror into this store"
    with Timer('Import %s' % mirror.project):
      try:
        projectid = self.project(mirror)
      except sqlite3.IntegrityError:
        # project already exists, delete its logs
        self.cursor.execute('''
          delete from files where commithash in
            (select hash from commits where project=?)''',
          (mirror.project,))
        self.cursor.execute('delete from commits where project=?',
          (mirror.project,))
      try:
        for commit in mirror.commits():
          commitid = self.commit(projectid, commit)
          for fileChange in mirror.changes(commit):
            self.file(commitid, fileChange)
        self.cursor.connection.commit()
      except:
        self.cursor.connection.rollback()
        print 'Failed to import', mirror
        raise
    print 'Storage used:\t%s' % fileSize(self.path)
