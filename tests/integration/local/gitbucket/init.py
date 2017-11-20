#!/usr/bin/env python3
# coding: utf-8

import requests

base_url = 'http://localhost:8080'

s = requests.Session()

# Sign in
s.get(base_url + '/signin?redirect=%2F')
s.post(base_url + '/signin', data={"userName": "root", "password": "root"})

# start ssh server
system_data = {
    "baseUrl": "http://localhost:8080",
    "information": "",
    "allowAccountRegistration": "false",
    "isCreateRepoOptionPublic": "true",
    "allowAnonymousAccess": "true",
    "activityLogLimit": "",
    "ssh": "on",
    "sshHost": "localhost",
    "sshPort": "29418",
}
s.post(base_url + '/admin/system', data=system_data)

# create test user
user_data = {
    "userName": "git-repo-user",
    "password": "user",
    "fullName": "git-repo-user",
    "mailAddress": "user@localhost"
}
s.post(base_url + '/admin/users/_newuser', data=user_data)

# create root repo
repo_data = {
    "owner": "root",
    "name": "repo",
    "description": "",
    "isPrivate": "false",
    "createReadme": "on"
}
s.post(base_url + '/new', data=repo_data)

# sign out
s.get(base_url + '/signout')

# sign in by user
s.get(base_url + '/signin?redirect=%2F')
s.post(base_url + '/signin', data={"userName": "git-repo-user", "password": "user"})

# create group
group_data ={
    "groupName": "group",
    "description": "",
    "memberName": "git-repo-user",
    "members": "git-repo-user:true"
}
s.post(base_url + '/groups/new', data=group_data)

# create Token
ret = s.post(base_url + '/git-repo-user/_personalToken', data={"note": "for test"})
html = ret.content.decode("utf-8")
find_text = "data-clipboard-text="
idx = html.find(find_text) + len(find_text) + 1
token = html[idx:idx + 40]

print("PRIVATE_KEY_GITBUCKET={}".format(token))

