
# For the impatient

Just run `repoblick plot bb`.  It gets the changesets of the first
twenty repositories at Bitbucket and generates a plot of when contributors
joined the projects.  Check your `~/.repoblick/output` directory for the
image file.

# Description

Repoblick does a number of things.
 - list projects in a repository (currently only Bitbucket)
 - download projects, either cloning the whole repository, or only a
   part of it upto a certain changeset
 - import log data into an sqlite database for later processing
 - convert a raw, almost normalized database to a more verbose
   statistical database for easier querying
 - plot statistical database using a built-in query or plain sql

 Since each step requires the previous ones, performing any of them will
 perform the previous ones, too.  Unless it was done earlier, or you
 explicitly tell repoblick not to (with the `--only-this-step` option).

# Usage

    repoblick <command> [options] <host> [project]*

    <host> can be a real host, like http://hg.example.com/foo, or an
    acronym, like bb for Bitbucket.

