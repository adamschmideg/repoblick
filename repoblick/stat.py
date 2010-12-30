from store import SqliteStore

def first_commits(dbpath):
  '''
  When contributors made their first commits in each project.
  '''
  store = SqliteStore(dbpath)
  query = '''
    create temp view if not exists rawfirstcommits as
      select c.projectid, c.id, c.date, c.author
      from (
        select author, projectid, min(date) as mindate
        from commits
        group by author, projectid
        ) as f,
        commits c
      where
       c.date=f.mindate and
       c.author=f.author and
       c.projectid=f.projectid;

    create temp view if not exists firstcommits as
      select f.*, (
        select count(*)
        from rawfirstcommits r
        where r.projectid=f.projectid and r.date<f.date) as rank
      from rawfirstcommits f;
    '''
  store.cursor.executescript(query)
  store.cursor.execute('select * from firstcommits order by projectid, rank', [])
  for rec in store.cursor:
    print rec


if __name__ == '__main__':
  second_contributor('/tmp/lof.sqlite')
