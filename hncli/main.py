#!/usr/bin/env python
'''
hncli -- Main entry point
'''
import sys
import getpass
import webbrowser

from .cli import HackerNews


def main():
    hncli = HackerNews()
    hncli.intro = "\n".join([
        "hncli :: command-line interface for Hacker News",
        "[running Python %s on %s]" % (
            sys.version.splitlines()[0], sys.platform),
        "Type 'help' for instructions "
        "or 'cd top' and 'ls' for front page stories.",
    ])

    hncli.doc_header = "Supported commands"
    hncli.undoc_header = "Other commands"
    hncli.misc_header = "Help topics"
    hncli.ruler = "*"

    hncli.cmdloop()


if __name__ == '__main__':
    main()