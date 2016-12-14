from requests import session
import json


class TestClass:

    def __init__(self):
        self.s = session()
        self.url = "http://127.0.0.1:5000"

    def test_signup(self):
        # user 1
        response = self.s.post(self.url + "/signup", data={"username": "test1", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["user"] == "test1"

        # user 2
        response = self.s.post(self.url + "/signup", data={"username": "test2", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["user"] == "test2"

        # duplicated user
        response = self.s.post(self.url + "/signup", data={"username": "test1", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Duplicated username!"

    def test_logout(self):
        response = self.s.get(self.url + "/logout")
        assert response.status_code == 200 and json.loads(response.text)["logout"] == "success"

        response = self.s.get(self.url + "/logout")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

        response = self.s.post(self.url + "/photos")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

        s.get(url+"/photos")
        if response.status_code != 200 or json.loads(response.text)["user"] is not None:
            print "Upload Error"


    print "# Log in"
    username = users.keys()[-1]
    response = s.post(url+"/login", data={"username": username, "password": users[username]})
    if response.status_code != 200 or json.loads(response.text)["user"] != username:
        print "Log in Error1"

    response = s.get(url+"/login")
    print response.status_code
    if response.status_code != 200 or json.loads(response.text)["user"] != username:
        print "Log in Error2"

    response = s.post(url+"/login", data={"username": "", "password": ""})
    if response.status_code != 200 or json.loads(response.text)["user"] != username:
        print "Log in Error3"


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
