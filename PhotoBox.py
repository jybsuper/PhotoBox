from flask import Flask, Response, request, session, escape
from pymongo import MongoClient
import hashlib
from cStringIO import StringIO
from pywebhdfs.webhdfs import PyWebHdfsClient
import json

app = Flask(__name__)
app.secret_key = '"\x9c\xb81\x1b\x15\xcczc[\r~\x99X\xbf\xa7Y\xd3\xa2\x99Q\xb3B\xef'
app.debug = True

db = MongoClient("localhost", 27017).photobox
hdfs = PyWebHdfsClient(host='127.0.0.1', port='50070', user_name='jyb')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        return json.dumps({"user": escape(session['username'])})
    elif request.method == 'POST':
        if db.users.count({"username": request.form['username'], "password": request.form['password']}):
            session['username'] = request.form['username']
            return json.dumps({"user": escape(session['username'])})
        else:
            return json.dumps({"user": None})
    else:
        return """
        <form action="/login" method="post">
            <p><input type=text name=username>
            <p><input type=text name=password>
            <p><input type=submit value=Login>
        </form>
    """


@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username', None)
        return json.dumps({"user": None})
    else:
        return json.dumps({"user": None})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if not db.users.count({"username": request.form['username']}):
            db.users.insert_one({"username": request.form['username'], "password": request.form['password'], "photos": []})
            session['username'] = request.form['username']
            return json.dumps({"user": request.form['username']})
        else:
            return json.dumps({"user": None})
    else:
        return """
        <form action="/signup" method="post">
            <p><input type=text name=username>
            <p><input type=text name=password>
            <p><input type=submit value=Login>
        </form>
    """


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if "username" not in session:
        return json.dumps({"user": None})
    elif request.method == 'POST':
        md5 = hashlib.md5()
        md5.update(StringIO(request.files['uploaded_file'].read()).getvalue())
        if db.photos.count({"md5": md5.hexdigest()}):
            photo_id = db.photos.find_one({"md5": md5.hexdigest()})["_id"]
        else:
            photo_id = db.photos.insert_one({"md5": md5.hexdigest()}).inserted_id
        photos = db.users.find_one({"username": session['username']})["photos"]
        if photo_id not in photos:
            photos.append(photo_id)
            db.users.update_one({"username": session['username']}, {"$set": {"photos": photos}})
            hdfs_save(StringIO(request.files['uploaded_file'].read()).getvalue(), md5.hexdigest())
        return json.dumps({"user": escape(session['username']), "md5": md5.hexdigest()})
    else:
        return """
            <form action='/upload' method='post' enctype='multipart/form-data'>
                 <input type='file' name='uploaded_file'>
                 <input type='submit' value='Upload'>
            </form>
        """


@app.route('/list', methods=['GET'])
def photo_list():
    if "username" not in session:
        return json.dumps({"user": None})
    else:
        photo_id = db.users.find_one({"username": session['username']})["photos"]
        return json.dumps({"photo"+str(i): db.photos.find_one(photo)["md5"] for i, photo in enumerate(photo_id)})


@app.route('/get/<md5>', methods=['GET'])
def get(md5):
    m = hashlib.md5()
    m.update(hdfs_get(md5))
    return json.dumps({"photo": m.hexdigest()})


def hdfs_save(f, name):
    hdfs.create_file(name, f)


def hdfs_get(name):
    return hdfs.read_file(name)


if __name__ == '__main__':
    app.run()
