from urllib2 import urlopen
import os

from lxml import html

from repoblick.utils import make_int, Timer

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
