#!/usr/bin/env python3

'''This module contains a function that extracts the revision numbers
from a parameter.sh file.
'''

import re

class GetRevision(dict):

    def __init__(self, filename):
        super().__init__()
        re_revision = re.compile(r"^ *export ([a-z0-0]+)_rev *= *(.*)$")
        with open(filename, encoding="utf8") as f_in:
            for line in f_in.readlines():
                grp = re_revision.match(line)
                if grp:
                    lib = grp.group(1).lower()
                    # Try to convert
                    try:
                        version = int(grp.group(2))
                    except ValueError:
                        version = grp.group(2)
                    self[lib] = version



# ============================================================================

if __name__ == "__main__":
    gr = GetRevision("./fcm-make/parameters.sh")
    for lib, version in gr.items():
        print(f"{lib} -> {version}")
