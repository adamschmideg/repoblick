"""
A command line interface to the full repoblick functionality
"""
import argparse
import os
import sys

import repolist

def init_dir(dir):
    "Create working directory if it doesn't exist"
    if not os.path.exists(dir):
        os.makedirs(dir)

def get_host_info(host, project=None):
    """Get host info if it can be found in KNOWN_HOSTS,
    or try to split `host` into meaningful chunks"""
    try:
        info = KNOWN_HOSTS[host].copy()
        info['project'] = project
    except KeyError:
        if host.startswith('http://') or host.startswith('https://'):
            raise ValueError('Remote host %s not supported' % host)
        dir, file = os.path.split(host)
        info = dict(name=dir.replace(os.path.sep, '-'),
            urnpattern='dir/%s', lister=repolist.LocalLister)
        info['project'] = project or file
    return info

def list_command(args):
    "List repositories and store their names and attributes"
    init_dir(args.dir)
    repolist.list_repos(args.host,
        db=os.path.join(args.dir, 'repolist.sqlite'),
        start_page=args.start_page, pages=args.pages)

def mirror_command(args):
    "Make a local mirror of repositories for later processing"
    pass

def log2db_command(args):
    "Process logs of repositories"
    pass

def plot_command(args):
    "Make a plot of log data"
    pass

def add_host_arg(parser):
    """Add an argument to parser, include a help text with know hosts"""
    parser.add_argument('host',
        help='Either a known host (%s), or a local path' \
            % ', '.join(sorted(repolist.KNOWN_HOSTS.keys())))

def add_project_arg(parser):
    """Add project as optional positional argument"""
    parser.add_argument('project', nargs='?',
        help='A specific project at the host.  If not given, all projects at host are used')
    
def main():
    """Process cmdline args and call the appropriate function"""
    parser = argparse.ArgumentParser(description='Explore version controlled repositories')
    parser.add_argument('-d', '--dir',
        help='Directory to store databases and repository mirrors',
        default=os.path.expanduser('~/.repoblick'))
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('list',
        help=list_command.__doc__)
    add_host_arg(list_parser)
    list_parser.add_argument('-s', '--start-page', default=1)
    list_parser.add_argument('-p', '--pages', default=1)
    list_parser.set_defaults(func=list_command)

    mirror_parser = subparsers.add_parser('mirror',
        help=mirror_command.__doc__)
    add_host_arg(mirror_parser)
    add_project_arg(mirror_parser)
    mirror_parser.set_defaults(func=mirror_command)

    log2db_parser = subparsers.add_parser('log2db',
        help=log2db_command.__doc__)
    add_host_arg(log2db_parser)
    add_project_arg(log2db_parser)
    log2db_parser.set_defaults(func=log2db_command)

    plot_parser = subparsers.add_parser('plot',
        help=plot_command.__doc__)
    add_host_arg(plot_parser)
    add_project_arg(plot_parser)
    plot_parser.set_defaults(func=plot_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
