from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)
app.debug = True

db = MongoClient("localhost", 27017).photobox


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
