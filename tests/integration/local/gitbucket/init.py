#!/usr/bin/env python
# coding: utf-8

import requests

base_url = 'http://localhost:8080'

s = requests.Session()

# Sign in
s.get(base_url + '/signin?redirect=%2F')
s.post(base_url + '/signin', data={"userName": "root", "password": "root"})

# create test user
user_data = {
    "userName": "user",
    "password": "user",
    "fullName": "user",
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
s.post(base_url + '/signin', data={"userName": "user", "password": "user"})

# create group
group_data ={
    "groupName": "group",
    "description": "",
    "memberName": "user",
    "members": "user:true"
}
s.post(base_url + '/groups/new', data=group_data)

# create Token
ret = s.post(base_url + '/user/_personalToken', data={"note": "for test"})
html = ret.content.decode("utf-8")
find_text = "data-clipboard-text="
idx = html.find(find_text) + len(find_text) + 1
token = html[idx:idx + 40]

print("PRIVATE_KEY_GITBUCKET={}".format(token))

