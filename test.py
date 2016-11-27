#coding=utf-8
__author__ = 'jyb'


from requests import session
import random
from string import letters
import json

s = session()
url = "http://127.0.0.1:5000"

print "# Create users"
s.get(url+"/signup")

users = dict()
for i in range(10):
    username = ''.join(random.sample(letters, i+5))
    pwd = ''.join(random.sample(letters, 6))
    users[username] = pwd
    response = s.post(url+"/signup", data={"username": username, "password": pwd})
    if response.status_code != 200 or json.loads(response.text)["user"] != username:
        print "Wrong user in signup"

for u, p in users.items():
    response = s.post(url+"/signup", data={"username": u, "password": p})
    if response.status_code != 200 or json.loads(response.text)["user"] is not None:
        print "Duplicate user Error"


print "# Log out"
response = s.get(url + "/logout")
if response.status_code != 200 or json.loads(response.text)["user"] is not None:
    print "Log out Error"
s.post(url + "/logout")
if response.status_code != 200 or json.loads(response.text)["user"] is not None:
    print "Log out Error"

s.get(url+"/list")
if response.status_code != 200 or json.loads(response.text)["user"] is not None:
    print "Get Photo list Error"

s.get(url+"/upload")
if response.status_code != 200 or json.loads(response.text)["user"] is not None:
    print "Upload Error"


print "# Log in"
username = users.keys()[-1]
response = s.post(url+"/login", data={"username": username, "password": users[username]})
if response.status_code != 200 or json.loads(response.text)["user"] != username:
    print "Log in Error"

response = s.get(url+"/login")
if response.status_code != 200 or json.loads(response.text)["user"] != username:
    print "Log in Error"

response = s.post(url+"/login", data={"username": "", "password": ""})
if response.status_code != 200 or json.loads(response.text)["user"] != username:
    print "Log in Error"


print "# upload"
image = {"uploaded_file": open("img1.jpeg", "rb")}
response = s.post(url+"/upload", files=image)
j = json.loads(response.text)
if response.status_code != 200 or j["user"] != username or "md5" not in j:
    print "Upload Error"

print "# get photos"
response = s.get(url+"/list")
if response.status_code != 200 or j["md5"] not in json.loads(response.text).values():
    print "Get list Error"

response = s.get(url+'/get/'+j["md5"])
if response.status_code != 200 or not json.loads(response.text)["photo"]:
    print "Get photo Error"
