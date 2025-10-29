
**Notable changes**

- The README has been updated to reflect that the standard compression format
  for gentoo binary packages (zstandard) is supported but only for Python
  3.14+.

- The cache used for stats has been converted to use GBP's new sitecache API.

- gbp-fl's GraphQL layer extend's GBP's `MachineSummary` type by adding a
  `fileStats` field which contains file-level stats of the machine's packages.

- gbp-fl's GraphQL layer removed the BinPkg type in favor of GBP's Package
  type.
