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

create temp view if not exists starts as
  select c.projectid, c.id as commitid, c.date
  from (
    select projectid, min(date) as mindate
    from commits
    group by projectid
    ) as f,
    commits c
  where
   c.date=f.mindate and
   c.projectid=f.projectid;

create temp table if not exists changes as
  select c.projectid as projectid, c.date as date, c.id as commitid,
      ch.lines as lines, ifnull(ch.addfiles,0) as addfiles, ifnull(ch.delfiles,0) as delfiles
  from
    commits c,
    (select f1.commitid, f1.lines, f2.addfiles, f3.delfiles
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
          on f1.commitid = f3.commitid) as ch
  where ch.commitid = c.id;

create temp view if not exists _fileaccums as
  select ch1.commitid, sum(ch2.lines) as lines, sum(ch2.addfiles-ch2.delfiles) as files
  from changes ch1, changes ch2
  where ch1.projectid=ch2.projectid and ch1.date>=ch2.date
  group by ch1.commitid;

create temp view if not exists _commitaccums as
  select c.projectid, c.id as commitid, (s.commitid-c.id) as ncommits, julianday(c.date)-julianday(s.date) as days
  from commits c, starts s
  where c.projectid=s.projectid;

create temp view if not exists accums as
  select ca.projectid, ca.commitid, ca.ncommits, ca.days, fa.lines, fa.files
  from _fileaccums fa, _commitaccums ca
  where ca.commitid=fa.commitid;
