## Steps to re-create test environment

 * `cd <path to git-repo>/tests/integration/local/gogs`
 * `./init_conf.sh` # this will change `custom/conf/app.ini` as repository/ROOT must be full path
 * `<path to gogs>/gogs web --config custom/conf/app.ini` # run with local config. Gitea also supported
 * `./init.sh` # this will create users, organizations and repositories required for testing. Server must be completely started (listeninig)

Under Windows cygwin bash required for scripts (mingw/msys not tested).
