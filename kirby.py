from __future__ import print_function

from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, Response

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from os import urandom
from datetime import datetime

from flask_wtf import Form
from flask_wtf.csrf import CsrfProtect

from wtforms import TextAreaField, BooleanField
from wtforms.validators import Length, InputRequired

import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

import string
CHARS = string.digits + string.ascii_letters

# TODO:
# * secret key
# * import tool (or keep same db?)
# * support creating (empty|new) db
# * recent public pastes
# * list of support languages
# * help page / usage
# * support themes through sessions
# * download paste


SECRET_KEY = 'foo'

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thedb.db'
app.secret_key = '\xecm\xba)I\xd8m\xc4(\x94\xf5\xf2\x1e\xff\xcap\x0cls\xe0\xc3k\x00\x86'


db = SQLAlchemy(app)
CsrfProtect(app)


# Lodge It db:
# CREATE TABLE pastes (
#        paste_id INTEGER NOT NULL,
#        code TEXT,
#        parent_id INTEGER,
#        pub_date DATETIME,
#        language VARCHAR(30),
#        user_hash VARCHAR(40),
#        handled BOOLEAN,
#        private_id VARCHAR(40),
#        PRIMARY KEY (paste_id),
#         UNIQUE (private_id),
#        FOREIGN KEY(parent_id) REFERENCES pastes (paste_id),
#        CHECK (handled IN (0, 1))
#);

#XXX To get syntax.css: HtmlFormatter().get_style_defs('.highlight')),


class Paste(db.Model):
    __tablename__ = 'pastes'

    paste_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.UnicodeText)
    parent_id = db.Column(db.ForeignKey('pastes.paste_id'), nullable=True)

    pub_date = db.Column(db.DateTime)
    language = db.Column(db.String(30))
    user_hash = db.Column(db.String(40), nullable=True)

    # ???
    handled = db.Column(db.Boolean)

    private_id = db.Column(db.String(40), unique=True, nullable=True)

    # Children
    #children = db.relation('Paste', cascade='all',
    #    primaryjoin=parent_id == paste_id,
    #    backref=db.backref('parent', remote_side=[paste_id]))

    # TODO: Parent handling, language handling
    def __init__(self, code, lang, private=None, parent=None):
        #if language not in LANGUAGES:
        #    language = 'text'
        if lang is None:
            lang = 'text'

        self.language = lang

        self.code = u'\n'.join(code.splitlines())

        if private is not None:
            self.private_id = private

        self.pub_date = datetime.now()

        #if parent is not None:
        #    if isinstance(parent, Paste):
        #        pass
        #        # TODO
        #    else:
        #        self.parent_id = parent

    def __repr__(self):
        return 'Paste(%s, %s)' % (self.paste_id, self.private_id)

    def get_pid(self):
        if self.private_id:
            return self.private_id
        return str(self.paste_id)
            
class PasteForm(Form):
    private =  BooleanField('private', [])
    paste = TextAreaField('paste', [InputRequired(), Length(min=5)])


@app.route('/')
def main():
    form = PasteForm()

    return render_template('newpaste.html', form=form,
            theme=request.args.get('t', 'default'))

def get_paste(paste):
    r = None

    try:
        pid = int(paste)
        r = db.session.query(Paste).filter(Paste.paste_id == pid).first()

    except ValueError:
        pid = paste
        r = db.session.query(Paste).filter(Paste.private_id == pid).first()

    if r is None:
        abort(404, 'No such paste')

    if r.private_id is not None:
        abort(403, 'Resource denied')

    return r


@app.route('/raw/<paste>', methods=['GET'])
def raw_paste(paste):
    r = get_paste(paste)

    return Response(r.code, mimetype='text/plain')


@app.route('/show/<paste>', methods=['GET'])
def view_paste(paste):
    r = get_paste(paste)

    lang = r.language if r.language != 'text' else request.args.get('l', None)
    theme = request.args.get('t', 'default')

    paste = r.code

    lexer = None
    if lang == None:
        try:
            lexer = guess_lexer(paste)
        except ClassNotFound:
            pass
    else:
        try:
            lexer = get_lexer_by_name(lang)
        except:
            abort(500, 'Invalid lexer: %s' % lang)

    if lexer is None:
        try:
            lexer = get_lexer_by_name('text')
        except:
            abort(500, 'Invalid lexer: %s' % lang)


    formatter = HtmlFormatter(linenos=True)#, cssclass='syntax')#, style='friendly')

    h = pygments.highlight(paste, lexer, formatter)

    return render_template('viewpaste.html', data=h, theme=theme)

@app.route('/paste', methods=['POST'])
def paste():
    form = PasteForm(request.form)

    if form.validate():
        for _ in xrange(10):
            if form.private.data:
                priv_id = ''.join(map(lambda x: CHARS[ord(x) % len(CHARS)], urandom(40)))

            code = form.paste.data

            try:
                p = Paste(code, lang=None, private=priv_id if form.private.data
                        else None)
                db.session.add(p)
                db.session.commit()
                return redirect('/show/%s' % p.get_pid())
            except IntegrityError as e:
                print('Failed to add paste:', p, e)

    abort(500, 'Failed to add paste')

if __name__ == '__main__':
    db.create_all()

    app.run(port=5001)
