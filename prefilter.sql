select project, lines, commits from (
  select project, max(lines) as lines, commits from (
    select p.project, p.commits, sum(f.added-f.deleted) as lines
      from projects p, commits c, files f
      where c.projectid=p.id and f.commitid=c.id
      group by c.id, p.id
    )
    group by project
  )
  where lines >= 0 and lines < 700 and commits > 50
  order by commits;
