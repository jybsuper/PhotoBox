from requests import session
import json
import hashlib

s = session()
url = "http://127.0.0.1:5000"

image = open("img1.jpeg", "rb").read()
md5 = hashlib.md5()
md5.update(image)
md5 = md5.hexdigest()

class TestClass:
    def test_signup(self):
        # user 1
        response = s.post(url + "/signup", data={"username": "test1", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["user"] == "test1"

        # user 2
        response = s.post(url + "/signup", data={"username": "test2", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["user"] == "test2"

        # duplicated user
        response = s.post(url + "/signup", data={"username": "test1", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Duplicated username!"

    def test_logout(self):
        response = s.get(url + "/logout")
        assert response.status_code == 200 and json.loads(response.text)["logout"] == "success"

        response = s.get(url + "/logout")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

        response = s.post(url + "/photos")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

        response = s.get(url + "/photos")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

        response = s.get(url + "/photos/test")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

        response = s.delete(url + "/photos/test")
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Not logged in!"

    def test_login(self):
        response = s.post(url + "/login", data={"username": "test1", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["user"] == "test1"

        s.get(url + "/logout")
        response = s.post(url + "/login", data={"username": "wrong", "password": "test"})
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Wrong password!"

        s.post(url + "/login", data={"username": "test1", "password": "test"})

    def test_upload(self):
        image = {"uploaded_file": open("img1.jpeg", "rb")}

        response = s.post(url + "/photos", files=image)
        assert response.status_code == 200 and json.loads(response.text)["photo_id"] == md5

        test_file = {"uploaded_file": open("api.py", "rb")}
        response = s.post(url + "/photos", files=test_file)
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Invalid format!"

    def test_photo_list(self):
        response = s.get(url+"/photos")
        assert response.status_code == 200 and md5 in json.loads(response.text)["photo_ids"]

    def test_get_delete(self):
        response = s.get(url + "/photos/" + md5)
        assert response.status_code == 200 and md5 in json.loads(response.text)["photo"] == image

        response = s.delete(url + "/photos/" + md5)
        assert response.status_code == 200 and md5 in json.loads(response.text)["delete"] == "success"

        response = s.get(url + "/photos/" + md5)
        assert response.status_code == 200 and md5 in json.loads(response.text)["er"] == "Photo not found!"

        response = s.delete(url + "/photos/" + md5)
        assert response.status_code == 200 and md5 in json.loads(response.text)["er"] == "Photo not found!"

    def test_authority(self):
        image = {"uploaded_file": open("img1.jpeg", "rb")}
        s.post(url + "/photos", files=image)
        s.get(url + "/logout")
        s.post(url + "/login", data={"username": "test2", "password": "test"})

        response = s.get(url + "/photos/" + md5)
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Permission denied!"

        response = s.delete(url + "/photos/" + md5)
        assert response.status_code == 200 and json.loads(response.text)["er"] == "Permission denied!"

# t = TestClass()
# t.test_signup()
# t.test_login()
# t.test_upload()
# t.test_photo_list()
# t.test_get_delete()
# t.test_authority()
