#!/bin/bash
echo "Checking user test-admin in Gogs on http://127.0.0.1:3000"
if ! python3 -c "import sys,gogs_client;up=gogs_client.UsernamePassword('test-admin','test-admin');s=gogs_client.GogsApi('http://127.0.0.1:3000');sys.exit(s.authenticated_user(up).user_id<1)" 2>/dev/null ; then
  echo "Creating admin user test-admin"
  gogs admin create-user --config custom/conf/app.ini --name=test-admin --password=test-admin --email=admin@gogs.loopback --admin=true
fi
echo "Checking user other in Gogs on http://127.0.0.1:3000"
if ! python3 -c "import sys,gogs_client;up=gogs_client.UsernamePassword('other','other');s=gogs_client.GogsApi('http://127.0.0.1:3000');sys.exit(s.authenticated_user(up).user_id<1)" 2>/dev/null ; then
  echo "Creating user other"
  gogs admin create-user --config custom/conf/app.ini --name=other --password=other --email=other@gogs.loopback
  python3 -c "import os,gogs_client,functools;up=gogs_client.UsernamePassword('other','other');s=gogs_client.GogsApi('http://127.0.0.1:3000');r=s.create_repo(up,'git-repo',readme_template='Default',license_template='MIT License',auto_init=True);print('\t'.join(map(str,(r.repo_id,r.full_name,r.urls.ssh_url))))"
fi
echo "Checking user git-repo-test in Gogs on http://127.0.0.1:3000"
if ! python3 -c "import sys,gogs_client;up=gogs_client.UsernamePassword('git-repo-test','git-repo-test');s=gogs_client.GogsApi('http://127.0.0.1:3000');sys.exit(s.authenticated_user(up).user_id<1)" 2>/dev/null ; then
  echo "Creating user git-repo-test"
  gogs admin create-user --config custom/conf/app.ini --name=git-repo-test --password=git-repo-test --email=guyzmo@gogs.loopback
fi
echo "Creating access token for user git-repo-test in Gogs on http://127.0.0.1:3000"
export PRIVATE_KEY_GOGS=`python3 -c "import gogs_client;up=gogs_client.UsernamePassword('git-repo-test','git-repo-test');s=gogs_client.GogsApi('http://127.0.0.1:3000');t=s.ensure_token(up, 'git-repo');print(t.token)"`
echo "PRIVATE_KEY_GOGS=$PRIVATE_KEY_GOGS"
git config --global --replace-all gitrepo.gogs.fqdn "http://127.0.0.1:3000"
git config --global --replace-all gitrepo.gogs.token "$PRIVATE_KEY_GOGS"
echo "Creating repository git-repo under user git-repo-test in Gogs on http://127.0.0.1:3000"
python3 -c "import os,gogs_client,functools;t=gogs_client.Token(os.environ['PRIVATE_KEY_GOGS']);s=gogs_client.GogsApi('http://127.0.0.1:3000');r=[functools.partial(s.create_repo,t,'git-repo',readme_template='Default',license_template='MIT License',gitignore_templates=['Python'],auto_init=True),functools.partial(s.get_repo,t,'git-repo-test','git-repo')][bool(s.repo_exists(t,'git-repo-test','git-repo'))]();print('\t'.join(map(str,(r.repo_id,r.full_name,r.urls.ssh_url))))"
echo "Creating organization guyzmo for user git-repo-test in Gogs on http://127.0.0.1:3000"
python3 -c "import os,gogs_client;t=gogs_client.Token(os.environ['PRIVATE_KEY_GOGS']);up=gogs_client.UsernamePassword('test-admin','test-admin');s=gogs_client.GogsApi('http://127.0.0.1:3000');r=s._get('/users/guyzmo',auth=t);r=[lambda:s._check_ok(s._post('/admin/users/git-repo-test/orgs',auth=up,json={'username':'guyzmo'})),lambda:r][r.ok]().json();print('\t'.join(map(str,(r['id'],r['username'],r['avatar_url']))))"
#curl -iu test-admin:test-admin -H "Content-Type: application/json" --data "{""username"":""guyzmo""}" http://127.0.0.1:3000/api/v1/admin/users/git-repo-test/orgs
echo "Creating repository git-repo under organization guyzmo in Gogs on http://127.0.0.1:3000"
python3 -c "import os,gogs_client,functools;t=gogs_client.Token(os.environ['PRIVATE_KEY_GOGS']);s=gogs_client.GogsApi('http://127.0.0.1:3000');r=[lambda:gogs_client.GogsRepo.from_json(s._check_ok(s._post('/org/guyzmo/repos',t,json=dict(name='git-repo',readme='Default',license='MIT License',gitignore='Node',auto_init=True))).json()),functools.partial(s.get_repo,t,'guyzmo','git-repo')][bool(s.repo_exists(t,'guyzmo','git-repo'))]();print('\t'.join(map(str,(r.repo_id,r.full_name,r.urls.ssh_url))))"
