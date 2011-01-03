from urllib2 import urlopen
import os

from lxml import html

from store import SqliteStore
from utils import Timer, make_int

class HostInfo:
    """Information about a host that is needed to mirror a repo from
    it.  It may include a lister class, too."""
    def __init__(self, name, urnpattern, shortname=None,
            lister_class=None, vcs=None, hostid=None):
        self.name = name
        self.urnpattern = urnpattern
        self.shortname = shortname
        self.lister_class = lister_class
        self.vcs = vcs
        self.hostid = hostid

    @staticmethod
    def _split_unknown_host(host):
        """Split a host not found in db to (host_info, project)
        >>> info, prj = HostInfo._split_unknown_host('http://example.com/foo/bar')
        >>> prj
        'foo/bar'
        >>> info.name
        'http/example-com'
        >>> info.urnpattern
        'http://example.com'
        >>> info, prj = HostInfo._split_unknown_host('http://repo.example.com')
        >>> prj
        >>> info.name
        'http/repo-example-com'
        >>> info, prj = HostInfo._split_unknown_host('/path/to/somewhere')
        >>> prj
        >>> info.name
        'local/path-to-somewhere'
        """
        # It may start with a protocol
        try:
            proto, rest = host.split('://')
            try:
                host_name, project = rest.split('/', 1)
            except ValueError:
                host_name = rest
                project = None
            name = '%s/%s' % (proto,
                host_name.replace('/', '-').replace('.', '-'))
            urnpattern = '%s://%s' % (proto, host_name)
        except ValueError:
            # It must be a local path
            urnpattern = host
            name = os.path.abspath(host).replace(os.path.sep, '-')
            if name.startswith('-'):
                name = name[1:]
            name = 'local/%s' % name
            project = None
        # Make a host_info
        host_info = HostInfo(name=name, urnpattern=urnpattern)
        return host_info, project

    @staticmethod
    def split_host(store, host):
        """Split a host name to (host_info, project) where project may
        be None if the whole name can be recognized as a host.  The
        host_info is guaranteed to be saved in store."""
        # Try an exact match
        store.cursor.execute('''
            select * from hosts where shortname=:host
            union
            select * from hosts where name=:host
            union
            select * from hosts where urnpattern=:host
            ''', dict(host=host))
        raw_info = store.cursor.fetchone()
        if raw_info:
            host_info = HostInfo(**raw_info)
            project = None
        else:
            # Try a partial match with urnpattern
            store.cursor.execute('''
                select * from hosts where :host like urnpattern || "%"
                ''', dict(host=host))
            raw_info = store.cursor.fetchone()
            if raw_info:
                host_info = HostInfo(**raw_info)
                project = host[len(host_info.urnpattern) + 1:]
            else:
                # It's an unknown host yet
                host_info = HostInfo._split_unknown_host(host)
                hostid, _ = store.add_host(host_info)
                host_info.hostid = hostid
        return host_info, project

class Lister:
    "Generic lister to list projects on a host"
    def __init__(self, urnpattern):
        self.urnpattern = urnpattern

    def get_url(self, project):
        "Get the full url of a project using the urnpattern"
        if '%s' in self.urnpattern:
            return self.urnpattern % project
        elif self.urnpattern.endswith('/'):
            return self.urnpattern + project
        else:
            return self.urnpattern + '/' + project


class LocalLister(Lister):
    """List repos located in local file system, used mainly for testing."""

    def list_repos(self, start_page, pages):
        """List subdirectories under self.path.  Ignore start_page and
        pages args"""
        #pylint: disable-msg=W0613
        for dirname in os.listdir(self.urnpattern):
            if os.path.isdir(os.path.join(self.urnpattern, dirname, '.hg')):
                yield dirname, {}

    def is_local(self):
        return True


class RemoteLister(Lister):
    def is_local(self):
        return False


class BitbucketWeb(RemoteLister):
    """List repos reading bitbucket web pages and parsing them"""

    def list_repos(self, start_page, pages):
        subpage = 'all/commits'
        for p in range(start_page, start_page + pages):
            url = 'https://bitbucket.org/repo/%s/%s' % (subpage, p)
            with Timer('Read %s' % url):
                page = html.parse(urlopen(url))
            projects = page.xpath("/html/body/div/div/ul[@id='repositories']/li/dl")
            for prj in projects:
                commits = make_int(prj.xpath("dd[@class='commits']/div/span[1]/a/text()")[0])
                followers = make_int(prj.xpath("dd[@class='followers']/div/span[1]/a/text()")[0])
                forks = make_int(prj.xpath("dd[@class='forks']/div/span[1]/a/text()")[0])
                link = prj.xpath("dd[@class='name']/a[2]/@href")[0]
                if link.startswith('http'):
                    schema, _, domain, user, project, _ = link.split('/')
                else:
                    _, user, project, _ = link.split('/')
                yield '%s/%s' % (user, project), dict(commits=commits, watchers=followers, forks=forks)


KNOWN_HOSTS = {
    'bitbucket': HostInfo(name='bitbucket', lister_class=BitbucketWeb, vcs='hg',
        urnpattern='https://bitbucket.org'),
    'bb': HostInfo(name='bitbucket', lister_class=BitbucketWeb, vcs='hg',
        urnpattern='https://bitbucket.org'),
    'googlecode-mercurial': HostInfo(name='googlecode-mercurial', lister_class=None,
        vcs='hg', urnpattern='https://%s.googlecode.com/hg/'),
    'gc-hg': HostInfo(name='googlecode-mercurial', lister_class=None,
        vcs='hg', urnpattern='https://%s.googlecode.com/hg/'),
    'googlecode-subversion': HostInfo(name='googlecode-subversion', lister_class=None,
        vcs='svn', urnpattern='http://svnplot.googlecode.com/svn/trunk/'),
    'gc-svn': HostInfo(name='googlecode-subversion', lister_class=None,
        vcs='svn', urnpattern='http://svnplot.googlecode.com/svn/trunk/'),
    'github': HostInfo(name='github', lister_class=None,
        vcs='git', urnpattern='https://github.com/%.git'),
    'gh': HostInfo(name='github', lister_class=None,
        vcs='git', urnpattern='https://github.com/%.git'),
}

def get_host_info(host):
    """Get a HostInfo instance using KNOWN_HOSTS"""
    try:
        host_info = KNOWN_HOSTS[host]
    except KeyError:
        if host.startswith('http://') or host.startswith('https://'):
            raise ValueError('Remote host %s not supported' % host)
        name = os.path.abspath(host).replace(os.path.sep, '-')
        if name.startswith('-'):
            name = name[1:]
        host_info = HostInfo(name=name, lister_class=LocalLister,
            vcs=None, urnpattern=host)
    return host_info

def get_host_info_and_projects(host, projects=None, from_file=None,
        query=None, start_page=1, pages=1, read_stored=None,
        db_dir=None):
    """Get host info and projects that belong to that host.  Projects
    can be provided on the command line in more ways, or if not given, they can be
    obtained from the host using a lister.  There are three cases
    - host and projects are given -- no lister will be used, only the
      given projects will be stored
    - a recognized host is given, but no projects -- the projects will
      be listed either using a lister, or read from database, depending
      on the value of read_stored.
    - an unknown host is given -- the host will be treated as a single
      project
    """
    all_projects = None
    host_info = KNOWN_HOSTS.get(host, None)
    if not host_info:
        if not(projects or from_file or query):
            # Split host to host_info and project
            host, project = os.path.split(host)
            all_projects = [project]
        name = os.path.abspath(host).replace(os.path.sep, '-')
        if name.startswith('-'):
            name = name[1:]
        host_info = HostInfo(name=name, urnpattern=host)
    store = SqliteStore(db_dir)
    hostid, _ = store.add_host(host_info.name, host_info.urnpattern)
        
    if from_file or query:
        all_projects = projects or []
        if from_file:
            with open(from_file) as project_file:
                all_projects += project_file.readlines()
        if query:
            store.cursor.execute(query, [])
            all_projects += [row[0] for row in store.cursor]
    elif not all_projects:
        if read_stored:
            store = SqliteStore(db_dir)
            store.cursor.execute('select name from projects where hostid=?',
                [hostid])
            all_projects = [row[0] for row in store.cursor]
        else:
            lister = host_info.lister_class(host_info.urnpattern)
            all_projects = lister.list_repos(start_page, pages)
    if not read_stored:
        for project_name in all_projects:
            store.add_project(hostid, project_name, None)
    return host_info, all_projects

def list_repos(host, db=None, start_page=1, pages=1):
    """List repos using lister.  If host is in KNOWN_HOSTS, use the class
    there.  Otherwise handle host as a local path.  If db_path is None, print them to screen."""
    host_info = get_host_info(host)
    if host_info.lister_class:
        lister = host_info.lister_class(host_info.urnpattern)
        with Timer('List repos at %s' % host):
            store = SqliteStore(db)
            hostid, _ = store.add_host(host_info.name, host_info.urnpattern)
            for repo in lister.list_repos(start_page, pages):
                store.add_project(hostid, repo[0], repo[1])
            store.commit()
    else:
        raise ValueError('No lister available for %s' % host)


if __name__ == '__main__':
   import doctest
   doctest.testmod()
