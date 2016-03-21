## Git-Repo: git services CLI utility

### Usage

Control your remote git hosting services from the `git` commandline. The usage is
very simple. To clone a new project, out of github, just issue:

    % git-repo hub clone guyzmo/git-repo

But that works also with a project from gitlab, bitbucket, or your own gitlab:

    % git-repo lab clone guyzmo/git-repo
    % git-repo bb clone guyzmo/git-repo
    % git-repo myprecious clone guyzmo/git-repo

If you want to can choose the default branch to clone:

    % git-repo lab clone guyzmo/git-repo master

Though sometimes, as you're starting a new project, you want to create a new
repository to push to:

    % git-repo hub create guyzmo/git-repo

actually the namespace is facultative, as per default you can (and want to)
only create new repositories within your own account.

You might also want to add an existing remote ref to your workspace, and that
can be easily done with:

    % git-repo lab add guyzmo/git-repo

Which will add `https://gitlab.com/guyzmo/git-repo` as the `gitlab` remote!

Finally, you can open the repository's page, using the `open` command:

    % git-repo lab open guyzmo/git-repo

### Installation

You can get the tool using pypi:

    % pip install git-repo

or by getting the sources and running:

    % python3 setup.py install

### Configuration

To configure `git-repo` you need to tweak your `~/.gitconfig`. For each service
you've got an account on, you have to make a section in the gitconfig:

    [gitrepo "gitlab"]
        private-key = YourVerySecretKey

    [gitrepo "github"]
        private-key = YourOtherVerySecretKey

    [gitrepo "bitbucket"]
        private-key = username:password

Here, we're setting the basics: just the private key. You'll notice that for bitbucket
the private key is your username and password seperated by a column. That's because
bitbucket does not offer throw away private keys for tools (I might implement BB's OAuth
at some point).

You also have the ability to set up an alias:

    [gitrepo "bitbucket"]
        alias = bit
        private-key = username:password

that will change the command you use for a name you'll prefer to handle actions
for the service you use:

    % git-repo bit clone guyzmo/git-repo

Also, you can setup your own gitlab self-hosted server, using that configuration:

    [gitrepo "myprecious"]
        type = gitlab
        private-key = YourSuperPrivateKey
        url = https://gitlab.example.org/

Finally, to make it really cool, you can make a few aliases in your gitconfig:

    [alias]
        hub = repo hub
        lab = repo lab
        bb = repo bb
        perso = repo perso

So you can run the tool as a git subcommand:

    git hub clone guyzmo/git-repo

### TODO

* [ ] make it possible to choose method (SSH or HTTPS)
* [ ] make a `git-repo fork` action that will:
    - make a fork on the remote repository
    - clone the fork locally
    - add both the fork and the forked as remotes
* [ ] add OAuth support for bitbucket
* for more features, write an issue or, even better, a PR!

### License

    Copyright ⓒ Bernard `Guyzmo` Pratz <guyzmo+git-repo@m0g.net>

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

See the LICENSE file for the full license.

♥
