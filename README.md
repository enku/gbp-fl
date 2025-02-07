# gbp-fl

A [pfl](https://www.portagefilelist.de/)-inspired plugin for [Gentoo Build
Publisher](https://github.com/enku/gentoo-build-publisher#readme).

Gentoo's binary packages (binpkgs) are all collected into Gentoo Build
Publisher "builds". The **gbp-fl** tool is both a plugin for Gentoo Build
Publisher and a CLI tool.

As a plugin for Gentoo Build Publisher, when builds are pushed to GBP, gbp-fl
indexes the files for all the packages in the build.  It also provides a
convenient [web
API](https://raw.githubusercontent.com/enku/screenshots/refs/heads/master/gbp-fl/graphql.png)
for querying the index.

As a CLI tool, gbp-fl provides a plugin for
[gbpcli](https://github.com/enku/gbpcli#readme) that adds the ability to
search the index from the command line. It queries the web API for doing so.
With the latest versions of Gentoo Build Publisher, it also provides the
ability to fetch the binpkgs directly from the GBP server.

## Rationale

I'm not sure that this is useful, but it was fun to work on. However it might
be nice to learn about what kinds of packages belong on different systems and
how they compare, for example. Or one might want to fetch a file from a
package on one machine to use on another.  Who knows.

## Installation

### Server Plugin

To use gbp-fl you must first install the plugin on the GBP server. This
assumes you already have a working Gentoo Build Publisher installation. If
not, refer to the GBP Install Guide first.

Install the gbp-fl package into the GBP instance:

```sh
cd /home/gbp
sudo -u gbp -H ./bin/pip install gbp-fl[server]
```

Restart the GBP web app and task workers.

```sh
systemctl restart gentoo-build-publisher-wsgi.service
systemctl restart gentoo-build-publisher-worker.service
```

### Client Plugin

To use the gbp-fl command-line interface requires the gbpcli tool.  The
recommended way to install it on non-servers is via
[pipx](https://packages.gentoo.org/packages/dev-python/pipx):

```sh
pipx install gbpcli
```

Then add gbp-fl to the gbpcli environment:

```sh
pipx inject gbpcli git+https://github.com/enku/gbp-fl.git
```

## Usage

From the server, files from builds will automatically get indexed when they
are pulled.  Builds that are purged from GBP are also automatically removed
from the files index.  In addition the GraphQL API is automatically provided
through the web interface.

From the command-line interface, the `fl` subcommand is automatically made
available after installation.

To search for files, for example.

```
$ gbp fl search <keyword>
```

This command will display any filenames that matching the keyword for all the
builds that are hosted on the Gentoo Build Publisher instance. To restrict the
search to an particular screen name, use the `-m` argument.

![screenshot](https://raw.githubusercontent.com/enku/screenshots/refs/heads/master/gbp-fl/search.svg)

The search command displays the machine, build, package and path of the files
that are a match. In addition the file size and timestamp are displayed.

The binpkg files can even be downloaded to the local machine using the `fetch`
command:

```
$ gbp fl fetch <pkgspec>
```

![screenshot](https://raw.githubusercontent.com/enku/screenshots/refs/heads/master/gbp-fl/fetch.svg)

Other commands are forthcoming, for example `gbp fl stats` to display
statistics about files in a given build/machine. `gbp fl fetch` will gain the
ability to fetch individual files from individual packages, etc.  Also the
"special"  `--mine` argument will be added to `gbp fl search`

## Architecture

gbp-fl us both a plugin for Gentoo Build Publisher (server) and gbpcli
(client), much like gbp-ps.

There are 4 main components to **gbp-fl**:

- The database layer where file metadata are indexes. There is an abstract
  interface for this with different backends able to support the interface.
  Currently there are Django ORM and memory (for testing) interfaces. In the
  future other interfaces may be added (perhaps
  [OpenSearch](https://opensearch.org/)?).

- The signal handling layer plugs into Gentoo Pubild Publisher's `postpull`
  and `postdelete` signals to index (and un-index) the builds as they come and
  go.

- The GraphQL layer plugs into Gentoo Build Publisher's GraphQL subsystem. This
  registers a few types and queries specific to gbp-fl and provides their
  respective resolvers.

- The CLI layer plugs into the gbpcli command-line interface to add the `fl`
  subcommand (and gbp-fl's own sub-subcommands) then it accesses the GraphQL
  interface on the server to make queries based on the commands.
