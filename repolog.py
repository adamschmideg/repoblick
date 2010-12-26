"""
Store repodata in a persistent format, like a database or csv files
"""
import time

class SqliteStore:

  def __init__(self, path):
    import sqlite3
    self.path = path
    self.connection = sqlite3.connect(path)
    tables = (
      '''
      projects (
        owner text,
        name text,
        id text primary key
      )''',
      '''
      commits (
        author text,
        date timestamp,
        hash text primary key,
        projectid text,
        foreign key(projectid) references projects(id)
      )''',
      '''
      files (
        file text,
        commithash text,
        changetype char(1),
        added integer,
        modified integer,
        deleted integer,
        foreign key(commithash) references commits(hash)
      )''',
    )
    for t in tables:
      try:
        self.connection.execute('create table if not exists %s;' % t)
      except sqlite3.OperationalError, e:
        print e, t
      
  def project(self, owner, name):
    id = '%s/%s' % (owner, name)
    self.connection.execute('insert into projects values(?, ?, ?)',
      (owner, name, id))
    return id

  def commit(self, author, date, hash, projectid):
    self.connection.execute('insert into commits values(?, ?, ?, ?)',
      (author, date, hash, projectid))
    return hash

  def file(self, file, hash, changetype, added, modified, deleted):
    self.connection.execute('insert into files values(?, ?, ?, ?, ?, ?)',
      (file, hash, changetype, added, modified, deleted))
    
