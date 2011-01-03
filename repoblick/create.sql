create table if not exists hosts (
  id integer primary key autoincrement,
  name text,
  shortname text,
  urnpattern text,
  lister_module text,
  vcs text,
  unique(name),
  unique(urnpattern)
);

create table if not exists projects (
  id integer primary key autoincrement,
  hostid integer,
  name text,
  status text,
  foreign key(hostid) references hosts(id),
  unique(hostid, name)
);

create table if not exists projectattrs (
  id integer primary key autoincrement,
  projectid integer,
  key text,
  value text,
  foreign key(projectid) references projects(id),
  unique(projectid, key)
);

create table if not exists commits (
  id integer primary key autoincrement,
  author text,
  date timestamp,
  hash text,
  message text,
  projectid integer,
  foreign key(projectid) references projects(id),
  unique(projectid, hash)
);

create table if not exists files (
  id integer primary key autoincrement,
  commitid integer,
  changetype char(1),
  added integer,
  deleted integer,
  file text,
  isbinary boolean,
  foreign key(commitid) references commits(id),
  unique(commitid, file)
);

-- recognized hosts
insert into hosts(shortname, name, urnpattern, vcs) values('bb', 'bitbucket', 'https://bitbucket.org', 'hg');
insert into hosts(shortname, name, urnpattern, vcs) values('gh', 'github', 'https://github.com/%s.git', 'git');
insert into hosts(shortname, name, urnpattern, vcs) values('gc-hg', 'googlecode-mercurial', 'https://%s.googlecode.com/hg/', 'hg');
insert into hosts(shortname, name, urnpattern, vcs) values('gc-svn', 'googlecode-subversion', 'http://%s.googlecode.com/svn/trunk/', 'svn');
