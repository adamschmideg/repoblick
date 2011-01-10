
# For the impatient

Mine Software Repositories with Repoblick.
Just run `repoblick plot bb`.  It gets the changesets of the first
twenty repositories at Bitbucket and generates a plot of when contributors
joined the projects.  Check your `~/.repoblick/output/bitbucket` directory for the
image file.

# Description

Repoblick does a number of things.

- List projects in a repository (currently only Bitbucket)
- Download projects, either cloning the whole repository, or only a
   part of it upto a certain changeset
- Import log data into an sqlite database for later processing
- Convert a raw, almost normalized database to a more verbose
   statistical database for easier querying
- Plot statistical database using a built-in query or plain sql

Since each step requires the previous ones, performing any of them will
perform the previous ones, too.  Unless it was done earlier, or you
explicitly tell repoblick not to (with the `--only-this-step` option).

# Usage

Running `repoblick/cmdline.py -h` prints

    usage: repoblick/cmdline.py [-h] {plot,statdb,list,splot,mirror,import} ...

    Explore version controlled repositories

    positional arguments:
      {plot,statdb,list,splot,mirror,import}
        list                List repositories and store their names and attributes
        mirror              Make a local mirror of repositories for later
                            processing
        import              Process logs of repositories and put them into the
                            database
        statdb              Convert logdata database to a statistical database
        plot                Make a plot of log data
        splot               Make a plot of a single project using SVNPlot (not
                            working yet)

    optional arguments:
      -h, --help            show this help message and exit


Running `repoblick/cmdline.py plot -h` prints

    usage: repoblick/cmdline.py plot [-h] [-d DIR] [-f FROM_FILE] [-o] [-c COMMITS]
                           [-s START_INDEX] [-i INDEX_COUNT] [-q QUERY]
                           host [projects [projects ...]]

    positional arguments:
      host                  Either a known host (see cmdline.py plot show hosts),
                            or a local path
      projects              A specific project at the host. If not given, all
                            projects at host are used

    optional arguments:
      -h, --help            show this help message and exit
      -d DIR, --dir DIR     Directory to store databases and repository mirrors
      -f FROM_FILE, --from-file FROM_FILE
                            File to read for projects
      -o, --only-this-step  Do not perform operations of previous steps even if
                            needed
      -c COMMITS, --commits COMMITS
                            Maximum number of commits to mirror
      -s START_INDEX, --start-index START_INDEX
                            Start listing at this index
      -i INDEX_COUNT, --index-count INDEX_COUNT
      -q QUERY, --query QUERY

# Requirements

On systems with a debian-style package management (Debian, Ubuntu, etc), run
`apt-get install python python-argparse python-pysqlite2 python-matplotlib mercurial`.
If you have python>=2.7, you won't need `argparse`, it's part of the standard library.
If all you want is crunch data without plotting, you won't need matplotlib.
