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

    create temp view if not exists changes as
      select f1.commitid, f1.lines, f2.addfiles, f3.delfiles
      from
        (select commitid, sum(added)-sum(deleted) as lines
        from files
        group by commitid) as f1
        left join 
          (select commitid, count(*) as addfiles
          from files
          where changetype='A'
          group by commitid) as f2
          on f1.commitid = f2.commitid
          left join 
            (select commitid, count(*) as delfiles
            from files
            where changetype='D'
            group by commitid) as f3
            on f1.commitid = f3.commitid;
    '''
  store.cursor.executescript(query)
  store.cursor.execute('select * from firstcommits order by projectid, rank', [])
  for rec in store.cursor:
    print rec


if __name__ == '__main__':
  second_contributor('/tmp/lof.sqlite')
