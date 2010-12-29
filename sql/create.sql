create table if not exists projects (
  -- id integer primary key autoincrement,
  id integer,
  project text,
  host text,
  commits integer,
  watchers integer,
  forks integer,
  language text,
  cloned integer
);

create table if not exists commits (
  -- id integer primary key autoincrement,
  id integer,
  author text,
  date timestamp,
  hash text,
  message text,
  projectid integer,
  foreign key(projectid) references projects(id)
);

create table if not exists files (
  -- id integer primary key autoincrement,
  id integer,
  commitid integer,
  changetype char(1),
  added integer,
  deleted integer,
  file text,
  isbinary boolean,
  foreign key(commitid) references commits(id)
);

.import sql/demodata/projects.csv projects
.import sql/demodata/commits.csv commits
.import sql/demodata/files.csv files
