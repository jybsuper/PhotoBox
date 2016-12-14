from flask import Flask, request, session
from pymongo import MongoClient
import hashlib
from cStringIO import StringIO
from pywebhdfs.webhdfs import PyWebHdfsClient
import json
from PIL import Image

app = Flask(__name__)
app.secret_key = '"\x9c\xb81\x1b\x15\xcczc[\r~\x99X\xbf\xa7Y\xd3\xa2\x99Q\xb3B\xef'
app.debug = True

db = MongoClient("localhost", 27017).photobox
hdfs = PyWebHdfsClient(host='127.0.0.1', port='50070', user_name='jyb')


@app.route('/login', methods=['POST'])
def login():
    if "username" in session:
        return json.dumps({"user": session['username']})
    if db.users.count({"username": request.form['username'], "password": request.form['password']}):
        session['username'] = request.form['username']
        return json.dumps({"user": session['username']})
    else:
        return json.dumps({"er": "Wrong password!"})


@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username', None)
        return json.dumps({"logout": "success"})
    else:
        return json.dumps({"er": "Not logged in!"})


@app.route('/signup', methods=['POST'])
def signup():
    if not db.users.count({"username": request.form['username']}):
        db.users.insert_one({"username": request.form['username'], "password": request.form['password'], "photos": []})
        session['username'] = request.form['username']
        return json.dumps({"user": request.form['username']})
    else:
        return json.dumps({"er": "Duplicated username!"})


@app.route('/photos', methods=['POST'])
def create():
    if "username" not in session:
        return json.dumps({"er": "Not logged in!"})
    photos = db.users.find_one({"username": session['username']})["photos"]

    image = StringIO(request.files['uploaded_file'].read())
    mime = Image.open(image).format.lower()
    if mime not in ("jpeg", "png", "gif"):
        return json.dumps({"er": "Invalid format!"})

    md5 = hashlib.md5()
    md5.update(image.getvalue())

    if not db.photos.count({"md5": md5.hexdigest()}):
        db.photos.insert_one({"md5": md5.hexdigest(), "mime": mime, "refer": 0})
        hdfs.create_file(md5.hexdigest(), image.getvalue())

    if md5.hexdigest() not in photos:
        refer = db.photos.find_one({"md5": md5.hexdigest()})["refer"]
        db.photos.update_one({"md5": md5.hexdigest()}, {"$set": {"refer": refer+1}})

        photos.append(md5.hexdigest())
        db.users.update_one({"username": session['username']}, {"$set": {"photos": photos}})
    return json.dumps({"photo_id": md5.hexdigest()})


@app.route('/photos/<photo_id>', methods=["GET"])
def get(photo_id):
    if "username" not in session:
        return json.dumps({"er": "Not logged in!"})
    elif not db.photos.count({"md5": photo_id}):
        return json.dumps({"er": "Photo not found!"})
    elif photo_id not in db.users.find_one({"username": session['username']})["photos"]:
        return json.dumps({"er": "Permission denied!"})

    photo_info = db.photos.find_one({"md5": photo_id})
    photo = hdfs.read_file(photo_id)
    return json.dumps({"photo": photo, "Content-Type": photo_info["mime"]})


@app.route('/photos/<photo_id>', methods=["DELETE"])
def delete(photo_id):
    if "username" not in session:
        return json.dumps({"er": "Not logged in!"})
    elif not db.photos.count({"md5": photo_id}):
        return json.dumps({"er": "Photo not found!"})
    elif photo_id not in db.users.find_one({"username": session['username']})["photos"]:
        return json.dumps({"er": "Permission denied!"})

    photos = db.users.find_one({"username": session['username']})["photos"]
    photos.remove(photo_id)
    db.users.update_one({"username": session['username']}, {"$set": {"photos": photos}})

    refer = db.photos.find_one({"md5": photo_id})["refer"]
    if refer == 1:
        db.photos.remove({"md5": photo_id})
        hdfs.delete_file_dir(photo_id)
    else:
        db.photos.update_one({"md5": photo_id}, {"$set": {"refer": refer-1}})

    return json.dumps({"delete": "success"})


@app.route('/photos', methods=['GET'])
def photo_list():
    if "username" not in session:
        return json.dumps({"er": "Not logged in!"})
    else:
        return json.dumps({"photo_ids": db.users.find_one({"username": session['username']})["photos"]})


if __name__ == '__main__':
    app.run()
