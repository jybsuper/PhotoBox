from flask import Flask, Response, request, session, escape
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
        return json.dumps({"user": escape(session['username'])})
    if db.users.count({"username": request.form['username'], "password": request.form['password']}):
        session['username'] = request.form['username']
        return json.dumps({"user": escape(session['username'])})
    else:
        return json.dumps({"user": None})


@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username', None)
        return json.dumps({"user": None})
    else:
        return json.dumps({"user": None})


@app.route('/signup', methods=['POST'])
def signup():
    if not db.users.count({"username": request.form['username']}):
        db.users.insert_one({"username": request.form['username'], "password": request.form['password'], "photos": []})
        session['username'] = request.form['username']
        return json.dumps({"user": request.form['username']})
    else:
        return json.dumps({"user": None})


@app.route('/photos', methods=['POST'])
def create():
    if "username" not in session:
        return json.dumps({"user": None})

    image = StringIO(request.files['uploaded_file'].read())
    mime = Image.open(image).format.lower()
    if mime not in ("jpeg", "png", "gif"):
        return json.dumps({"photo_id": None})

    md5 = hashlib.md5()
    md5.update(image.getvalue())
    if db.photos.count({"md5": md5.hexdigest()}):
        photo_id = db.photos.find_one({"md5": md5.hexdigest()})["_id"]
    else:
        photo_id = db.photos.insert_one({"md5": md5.hexdigest(), "mime": mime}).inserted_id
    photos = db.users.find_one({"username": session['username']})["photos"]

    if photo_id not in photos:
        photos.append(photo_id)
        db.users.update_one({"username": session['username']}, {"$set": {"photos": photos}})
        hdfs.create_file(image.getvalue(), md5.hexdigest())
    return json.dumps({"photo_id": md5.hexdigest()})


@app.route('/photos/<photo_id>', methods=["GET"])
def get(photo_id):
    photo_info = db.photos.find_one({"md5": photo_id})
    if photo_info is None:
        return json.dumps({"photo": None, "Content-Type": None})
    photo = hdfs.read_file(photo_id)
    return json.dumps({"photo": photo, "Content-Type": photo_info["mime"]})


@app.route('/photos/<photo_id>', methods=["DELETE"])
def delete(photo_id):
    hdfs.delete_file_dir(photo_id)
    return json.dumps({})


@app.route('/photos', methods=['GET'])
def photo_list():
    if "username" not in session:
        return json.dumps({"user": None})
    else:
        photo_id = db.users.find_one({"username": session['username']})["photos"]
        return json.dumps({"photo_ids": [db.photos.find_one(photo)["md5"] for photo in photo_id]})


if __name__ == '__main__':
    app.run()
