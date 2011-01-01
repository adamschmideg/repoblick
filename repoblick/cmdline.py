import argparse
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick import repolist

def main():
    """Process cmdline args and call the appropriate function"""
    parser = argparse.ArgumentParser(description='Explore version controlled repositories',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--dir',
        help='Directory to store databases and repository mirrors',
        default=os.path.expanduser('~/.repoblick'))
    parser.add_argument('-c', '--count', default=None,
        help='max number of commits')
    parser.add_argument('command',
        choices=['list', 'mirror', 'log2db', 'plot'],
        help='' +
            'list\tList repositories and store their names and attributes\n' +
            'mirror\tMake a local mirror of repositories for later processing\n' +
            'log2db\tProcess logs of repositories\n' +
            'plot\tMake a plot of log data')
    parser.add_argument('host',
        help='Either a known host (%s), or a local path' \
            % ', '.join(repolist.KNOWN_HOSTS.keys()))
    parser.add_argument('project', nargs='?',
        help='A specific project at the host.  If not given, all projects at host are used')

    args = parser.parse_args()
    print 'args', args


if __name__ == '__main__':
    main()
