Bibtex completer
================

This is a simple Bibtex completer working with youcompleteme for vim.

Installation
------------

Git clone the program:

```bash
git clone https://github.com/Acanthostega/bibtex-completer
cd bibtex-completer
```

Run `./install.sh` in the directory of installation and follow the
instructions if problems.

If not already done, install `bibtexparser` module for python 2.x (used by
YouCompleteMe).

```bash
pip install bibtexparser --user # --user for local installation
```

Configuration
-------------

Put a file named `.bibtex_completer.json` in `json` format in the root
directory of your latex document, or upper in the tree structure. The
program will up in the tree until finding this configuration file.

Inside put a dictionary with the key "bibtex" containing the list of files
used for the bibtex references.

```json
{
    "bibtex": [ "path/to/reference.bib", "/path/to/second/references.bib"],
    "root": "path",
}
```

The `root` key is used for the root directory to search in `.tex` files for
labels. If not specified, it will be the directory where the used
configuration file is placed.

Recommandations
---------------

YouCompleteMe doesn't like non ASCII characters and so they are dropped from
the `bib` files. DON'T USE IT IN KEY IDENTIFIER IN THE BIBTEX FILES. The
corresponding key will not be the good one.
