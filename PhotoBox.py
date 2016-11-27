from flask import Flask, Response, request, session, escape
from pymongo import MongoClient
import hashlib
from cStringIO import StringIO
from pywebhdfs.webhdfs import PyWebHdfsClient

app = Flask(__name__)
app.secret_key = '"\x9c\xb81\x1b\x15\xcczc[\r~\x99X\xbf\xa7Y\xd3\xa2\x99Q\xb3B\xef'
app.debug = True

db = MongoClient("localhost", 27017).photobox
hdfs = PyWebHdfsClient(host='127.0.0.1', port='50070', user_name='jyb')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        return "Logged in as %s" % escape(session['username'])
    elif request.method == 'POST':
        if db.users.count({"username": request.form['username'], "password": request.form['password']}):
            session['username'] = request.form['username']
            return "Logged in as %s" % escape(session['username'])
        else:
            return "Wrong username or password!"
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
        return "Logged out"
    else:
        return "You are not logged in."


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if not db.users.count({"username": request.form['username']}):
            db.users.insert_one({"username": request.form['username'], "password": request.form['password'], "photos": []})
            session['username'] = request.form['username']
            return "Success"
        else:
            return "Please try another username"
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
        return "You are not logged in."
    elif request.method == 'POST':
        md5 = hashlib.md5()
        md5.update(request.files['uploaded_file'].read())
        if db.photos.count({"md5": md5.hexdigest()}):
            photo_id = db.photos.find_one({"md5": md5.hexdigest()})["_id"]
        else:
            photo_id = db.photos.insert_one({"md5": md5.hexdigest()}).inserted_id
        photos = db.users.find_one({"username": session['username']})["photos"]
        if photo_id not in photos:
            photos.append(photo_id)
            db.users.update_one({"username": session['username']}, {"$set": {"photos": photos}})
            hdfs_save(StringIO(request.files['uploaded_file'].read()), md5.hexdigest())
        return "Success"
    else:
        return """
            <!doctype html>
            <html>
            <body>
            <form action='/upload' method='post' enctype='multipart/form-data'>
                 <input type='file' name='uploaded_file'>
                 <input type='submit' value='Upload'>
            </form>
        """


@app.route('/index', methods=['GET'])
def index():
    if "username" not in session:
        return "You are not logged in."
    else:
        photos = db.users.find_one({"username": session['username']})["photos"]
        names = [db.photos.find_one(photo)["md5"] for photo in photos]
        photos = hdfs_get(names)
        return Response(photos[0], mimetype='image/jpeg')


def hdfs_save(f, name):
    hdfs.create_file(name, f)


def hdfs_get(names):
    return [hdfs.read_file(name) for name in names]


if __name__ == '__main__':
    app.run()
