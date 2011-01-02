from urllib2 import urlopen
import os

from lxml import html

from store import SqliteStore
from utils import Timer, make_int

class LocalLister:
    """List repos located in local file system, used mainly for testing."""

    def __init__(self, path):
        self.path = path
        self.urn_pattern = path + '/%s'
        self.name = path.replace(os.path.sep, '-')[1:]

    def list_repos(self, start_page, pages):
        """List subdirectories under self.path.  Ignore start_page and
        pages args"""
        #pylint: disable-msg=W0613
        for dir_ in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path, dir_, '.hg')):
                yield dir_, {}

    def is_local(self):
        return True


class RemoteLister:
    def is_local(self):
        return False


class BitbucketWeb(RemoteLister):
    """List repos reading bitbucket web pages and parsing them"""

    def __init__(self):
        self.urn_pattern = 'https://bitbucket.org/%s'
        self.name = 'bitbucket'
        
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
    'bitbucket': dict(name='bitbucket', lister=BitbucketWeb, vcs='hg',
        urnpattern='https://bitbucket.org/%s'),
    'bb': dict(name='bitbucket', lister=BitbucketWeb, vcs='hg',
        urnpattern='https://bitbucket.org/%s'),
    'googlecode-mercurial': dict(name='googlecode-mercurial', lister=None,
        vcs='hg', urnpattern='https://%s.googlecode.com/hg/'),
    'gc-hg': dict(name='googlecode-mercurial', lister=None,
        vcs='hg', urnpattern='https://%s.googlecode.com/hg/'),
    'googlecode-subversion': dict(name='googlecode-subversion', lister=None,
        vcs='svn', urnpattern='http://svnplot.googlecode.com/svn/trunk/'),
    'gc-svn': dict(name='googlecode-subversion', lister=None,
        vcs='svn', urnpattern='http://svnplot.googlecode.com/svn/trunk/'),
    'github': dict(name='github', lister=None,
        vcs='git', urnpattern='https://github.com/%.git'),
    'gh': dict(name='github', lister=None,
        vcs='git', urnpattern='https://github.com/%.git'),
}

def get_lister(host):
    """Get a lister for this host"""
    try:
        return KNOWN_HOSTS[host]()
    except KeyError:
        return LocalLister(host)

def list_repos(host, db=None, start_page=1, pages=1):
    """List repos using lister.  If host is in KNOWN_HOSTS, use the class
    there.  Otherwise handle host as a local path.  If db_path is None, print them to screen."""
    lister = get_lister(host)
    if db:
        with Timer('List repos at %s' % host):
            store = SqliteStore(db)
            hostid, _ = store.add_host(lister.name, lister.urn_pattern)
            for repo in lister.list_repos(start_page, pages):
                store.add_project(hostid, repo[0], repo[1])
            store.commit()
    else:
        print lister.name, lister.urn_pattern
        for repo in lister.list_repos(start_page, pages):
            print repo
