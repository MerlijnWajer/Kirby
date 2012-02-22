from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, Response

from flaskext.sqlalchemy import SQLAlchemy

SECRET_KEY = 'foo'
DEBUG = True
USERNAME = 'foo'
PASSWORD = 'foo'
SQL_DATABASE_URI = 'sqlite:////tmp/test.db'

app = Flask(__name__)
app.config.from_object(__name__)

db = SQLAlchemy(app)

class User(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

class Paste(db.Model):
    pid = db.Column(db.Integer, primary_key=True)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/v/<paste>')
def view_paste(paste):
    # Lookup paste
    pass

@app.route('/paste', methods=['POST'])
def paste():
    # Paste
    pass

if __name__ == '__main__':

    from werkzeug.contrib.cache import SimpleCache
    cache = SimpleCache()

    app.run()
