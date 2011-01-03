"""
A command line interface to the full repoblick functionality
"""
import argparse
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick import repolist, HostInfo
from repoblick.store import SqliteStore
from repoblick.utils import mkdirs, Timer

def list_command(args):
    "List repositories and store their names and attributes"
    store = SqliteStore(args.dir)
    host_info, project = repolist.split_host(store, args.host)
    all_projects = [project] if project else []
    all_projects += args.projects
    if args.from_file:
        with open(args.from_file) as project_file:
            all_projects += project_file.readlines()
    if all_projects:
        for prj in all_projects:
            store.add_project(host_info.id, prj, {})
        store.commit()
    elif host_info.lister_module:
        # Try to get lister
        lister = __import__(host_info.lister_module, fromlist=['list_repos'])
        with Timer('List repos at %s' % host_info.name):
            for repo in lister.list_repos(host_info, args.start_page, args.pages):
                store.add_project(host_info.id, repo[0], repo[1])
            store.commit()
    else:
        print 'Warning: No lister available for %s' % host_info.name

def mirror_command(args):
    "Make a local mirror of repositories for later processing"
    print 'Not implemented yet', args

def log2db_command(args):
    "Process logs of repositories"
    print 'Not implemented yet', args

def plot_command(args):
    "Make a plot of log data"
    print 'Not implemented yet', args

def splot_command(args):
    "Make a plot of a single project using SVNPlot"
    print 'Not implemented yet', args

def _add_common_arguments(parser):
    "Add host and projects arguments to subparser"
    parser.add_argument('host',
        help='Either a known host (see %(prog)s show hosts), or a local path')
    parser.add_argument('projects', nargs='*',
        help='A specific project at the host.  If not given, all projects at host are used')

def main():
    """Process cmdline args and call the appropriate function"""
    parser = argparse.ArgumentParser(description='Explore version controlled repositories')
    parser.add_argument('-d', '--dir',
        help='Directory to store databases and repository mirrors',
        default=os.path.expanduser('~/.repoblick'))
    parser.add_argument('-f', '--from-file',
        help='File to read for projects')
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('list',
        help=list_command.__doc__)
    _add_common_arguments(list_parser)
    list_parser.add_argument('-s', '--start-page', default=1)
    list_parser.add_argument('-p', '--pages', default=1)
    list_parser.set_defaults(func=list_command)

    mirror_parser = subparsers.add_parser('mirror',
        help=mirror_command.__doc__)
    mirror_parser.set_defaults(func=mirror_command)

    log2db_parser = subparsers.add_parser('log2db',
        help=log2db_command.__doc__)
    log2db_parser.set_defaults(func=log2db_command)

    plot_parser = subparsers.add_parser('plot',
        help=plot_command.__doc__)
    plot_parser.set_defaults(func=plot_command)

    splot_parser = subparsers.add_parser('splot',
        help=splot_command.__doc__)
    splot_parser.add_argument('-g', '--graph-dir',
        help='Where to generate graphs (default: %(default)s)',
        default='/tmp/graph')
    splot_parser.add_argument('-s', '--svnplot-db',
        help='Location of svnplot-specific database to be generated (default: %(default)s)',
        default='/tmp/svnplot.sqlite')
    splot_parser.set_defaults(func=splot_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
