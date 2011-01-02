from urllib2 import urlopen
import os

from lxml import html

from store import SqliteStore
from utils import Timer, make_int

class HostInfo:
    """Information about a host that is needed to mirror a repo from
    it.  It may include a lister class, too."""
    def __init__(self, name, lister_class, vcs, urnpattern):
        self.name = name
        self.lister_class = lister_class
        self.vcs = vcs
        self.urnpattern = urnpattern


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

def list_repos(host, db=None, start_page=1, pages=1):
    """List repos using lister.  If host is in KNOWN_HOSTS, use the class
    there.  Otherwise handle host as a local path.  If db_path is None, print them to screen."""
    host_info = get_host_info(host)
    lister = host_info.lister_class(host_info.urnpattern)
    if db:
        with Timer('List repos at %s' % host):
            store = SqliteStore(db)
            hostid, _ = store.add_host(host_info.name, host_info.urnpattern)
            for repo in lister.list_repos(start_page, pages):
                store.add_project(hostid, repo[0], repo[1])
            store.commit()
    else:
        for repo in lister.list_repos(start_page, pages):
            print repo
