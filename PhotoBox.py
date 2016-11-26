from flask import Flask, make_response, session, request, session, escape
from pymongo import MongoClient
from hdfs import Config
import hashlib
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = '"\x9c\xb81\x1b\x15\xcczc[\r~\x99X\xbf\xa7Y\xd3\xa2\x99Q\xb3B\xef'
app.debug = True

db = MongoClient("localhost", 27017).photobox
hdfs = Config().get_client('dev')


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
            hdfs_save(request.files['uploaded_file'], md5.hexdigest())
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
        photos = [db.photos.find_one(photo)["md5"] for photo in photos]
        return str(hdfs_get(photos))


def hdfs_save(f, name):
    f.save(os.path.join("static", name+'.jpg'))


def hdfs_get(names):
    return names


if __name__ == '__main__':
    app.run()
