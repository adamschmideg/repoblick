#!/usr/bin/env python
"""
A command line interface to the full repoblick functionality
"""
import argparse
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick import plot
from repoblick.command import _split_host, import_log, mirror_repo
from repoblick.store import SqliteStore
from repoblick.utils import mkdirs, relative_file, Timer

def _host_info_and_projects(store, args):
    "Get host_info and projects from command line"
    host_info, prj = _split_host(store, args.host)
    projects = [prj] if prj else []
    projects += args.projects
    if args.from_file:
        if os.path.isfile(args.from_file):
            with open(args.from_file) as project_file:
                projects += [line.strip() for line in project_file.readlines()]
        else:
            raise argparse.ArgumentError(None,
                '%s is not a readable file' % args.from_file)
    return host_info, projects

def _projects_from_store(store, host_info):
    "Get project names at host from database"
    return [prj['name'] for prj in store.get_projects(host_info)]

def list_command(args):
    "List repositories and store their names and attributes"
    store = SqliteStore(args.dir)
    host_info, projects = _host_info_and_projects(store, args)
    if projects:
        for prj in projects:
            store.add_project(host_info.id, prj, {})
        store.commit()
    elif host_info.lister_module:
        # Try to get lister
        lister = __import__(host_info.lister_module, fromlist=['list_repos'])
        with Timer('List repos at %s' % host_info.name):
            for repo in lister.list_repos(host_info, args.start_index, args.index_count):
                store.add_project(host_info.id, repo[0], repo[1])
            store.commit()
    else:
        print 'Warning: No lister available for %s' % host_info.name

def mirror_command(args):
    "Make a local mirror of repositories for later processing"
    store = SqliteStore(args.dir)
    host_info, projects = _host_info_and_projects(store, args)
    if not projects:
        projects = _projects_from_store(store, host_info)
    if not projects and not args.only_this_step:
        # Try to get a listing of projects
        list_command(args)
        projects = _projects_from_store(store, host_info)
    if projects:
        for prj in projects:
            source = host_info.project_remote_url(prj)
            dest = host_info.project_local_path(args.dir, prj)
            with Timer('Mirror %s' % (source)):
                mirror_repo(source, dest, max_commits=args.commits)
    else:
        print 'Warning: No projects found or given'

def import_command(args):
    "Process logs of repositories and put them into the database"
    store = SqliteStore(args.dir)
    host_info, projects = _host_info_and_projects(store, args)
    if not projects:
        projects = _projects_from_store(store, host_info)
    if not projects and not args.only_this_step:
        list_command(args)
        projects = _projects_from_store(store, host_info)
    if projects:
        for prj in projects:
            projectid, _ = store.add_project(host_info.id, prj)
            path = host_info.project_local_path(args.dir, prj)
            if not os.path.exists(os.path.join(path, '.hg')) and not args.only_this_step:
                source = host_info.project_remote_url(prj)
                mirror_repo(source, path)
            with Timer('Process logs %s' % (path)):
                import_log(store, projectid, path)

def statdb_command(args):
    "Convert logdata database to a statistical database"
    store = SqliteStore(args.dir)
    host_info, projects = _host_info_and_projects(store, args)
    if not projects:
        projects = _projects_from_store(store, host_info)
    if not projects and not args.only_this_step:
        import_command(args)
        projects = _projects_from_store(store, host_info)
    # TODO: convert only projects affected
    statdb = os.path.join(args.dir, 'statdb.sqlite')
    store.cursor.execute('attach database "%s" as stat' % statdb, [])
    script_file = relative_file(__file__, 'stat.sql')
    with Timer('Create statistical database'):
        with open(script_file) as script:
            store.cursor.executescript(script.read())

def plot_command(args):
    "Make a plot of log data"
    store = SqliteStore(args.dir)
    host_info, projects = _host_info_and_projects(store, args)
    if not projects:
        projects = _projects_from_store(store, host_info)
    if not projects and not args.only_this_step:
        statdb_command(args)
        projects = _projects_from_store(store, host_info)
    # TODO: plot only selected projects
    statdb = os.path.join(args.dir, 'statdb.sqlite')
    store.cursor.execute('attach database "%s" as stat' % statdb, [])
    image_dir = os.path.join(args.dir, 'output', host_info.name)
    mkdirs(image_dir)
    with Timer('Generate plots to %s' % image_dir):
        if args.query:
            plot.custom_queries(store, image_dir, args.query)
        else:
            plot.first_commits(store, image_dir)

def splot_command(args):
    "Make a plot of a single project using SVNPlot (not working yet)"
    print 'Not implemented yet', args

def _add_common_arguments(parser):
    "Add host and projects arguments to subparser"
    parser.add_argument('host',
        help='Either a known host (see %(prog)s show hosts), or a local path')
    parser.add_argument('projects', nargs='*',
        help='A specific project at the host.  If not given, all projects at host are used')

def make_parser():
    """Get a command line parser with all subparsers, defaults, etc
    configured"""
    parser = argparse.ArgumentParser(description='Explore version controlled repositories')
    subparsers = parser.add_subparsers()
    list_parser = subparsers.add_parser('list',
        help=list_command.__doc__)
    list_parser.set_defaults(func=list_command)
    mirror_parser = subparsers.add_parser('mirror',
        help=mirror_command.__doc__)
    mirror_parser.set_defaults(func=mirror_command)
    import_parser = subparsers.add_parser('import',
        help=import_command.__doc__)
    import_parser.set_defaults(func=import_command)
    statdb_parser = subparsers.add_parser('statdb',
        help=statdb_command.__doc__)
    statdb_parser.set_defaults(func=statdb_command)
    plot_parser = subparsers.add_parser('plot',
        help=plot_command.__doc__)
    plot_parser.set_defaults(func=plot_command)
    splot_parser = subparsers.add_parser('splot',
        help=splot_command.__doc__)
    splot_parser.set_defaults(func=splot_command)

    for prs in [list_parser, mirror_parser, import_parser, statdb_parser, plot_parser]:
        prs.add_argument('host',
            help='Either a known host (see %(prog)s show hosts), or a local path')
        prs.add_argument('projects', nargs='*',
            help='A specific project at the host.  If not given, all projects at host are used')
        prs.add_argument('-d', '--dir',
            help='Directory to store databases and repository mirrors',
            default=os.path.expanduser('~/.repoblick'))
        prs.add_argument('-f', '--from-file',
            help='File to read for projects')
        prs.add_argument('-o', '--only-this-step',
            help='Do not perform operations of previous steps even if needed',
            action='store_true')
        prs.add_argument('-c', '--commits',
            help='Maximum number of commits to mirror', type=int)
        prs.add_argument('-s', '--start-index',
            help='Start listing at this index', default=1, type=int)
        prs.add_argument('-i', '--index-count', default=1, type=int)

    plot_parser.add_argument('-q', '--query',
        action='append')

    splot_parser.add_argument('-g', '--graph-dir',
        help='Where to generate graphs (default: %(default)s)',
        default='/tmp/graph')
    splot_parser.add_argument('-s', '--svnplot-db',
        help='Location of svnplot-specific database to be generated (default: %(default)s)',
        default='/tmp/svnplot.sqlite')
    return parser


if __name__ == '__main__':
    arg_parser = make_parser()
    args = arg_parser.parse_args()
    args.func(args)
