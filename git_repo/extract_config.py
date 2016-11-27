#!/usr/bin/env python3

import os
import sys
import git

def extract_gitrepo_sections(conf):
    return filter(lambda k: k.startswith('gitrepo'), conf.sections())

def extract_gitrepo_conf(gconf_old, gconf_new):
    if os.path.exists(gconf_new):
        return "✗ cannot execute, file already exists: {}".format(gconf_new)
    with git.config.GitConfigParser(gconf_old, read_only=False) as cold:
        with git.config.GitConfigParser(gconf_new, read_only=False) as cnew:
            sections = list(extract_gitrepo_sections(cold))
            # copy the sections to the new configuration file
            cnew.update({s: {k:v for k,v in cold.items(s)} for s in sections})
            cnew.write()
            # remove the sections from the old configuration file
            for section in sections:
                cold.remove_section(section)
            # insert path to the new config file in the old one
            cold.update({'include': {'path': os.path.abspath(gconf_new)}})
    print("🍻 git-repo configuration extracted to new file: {}".format(gconf_new))

if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        sys.exit('Usage: {} [.gitconfig-repos] [.gitconfig]'.format(sys.argv[0]))
    sys.exit(extract_gitrepo_conf(
        gconf_old=os.path.expanduser(len(sys.argv) >= 3 and sys.argv[2] or '~/.gitconfig'),
        gconf_new=os.path.expanduser(len(sys.argv) >= 2 and sys.argv[1] or '~/.gitconfig-repos')
    ))


