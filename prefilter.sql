select project, max(lines) as lines, commits from (
  select p.project, p.commits, c.date, sum(f.added-f.deleted) as lines
    from projects p, commits c, files f
    where c.projectid=p.id and f.commitid=c.id
    group by c.id
    order by lines
  )
  where lines >= 0 and lines < 700 and commits > 50
  group by project
  order by commits;
