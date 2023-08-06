import os
import requests
from flask import Flask, request, render_template, redirect, flash, session, jsonify, g
from routes.list import list
from routes.auth import auth
from routes.user import user
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, List, Listings, Anime
from forms import SignUpForm, LoginForm, EditUserForm
from app import *
from secret import API_KEY_CONFIG

CURR_USER_KEY = "curr_user"

app = Flask(__name__) 
app.register_blueprint(list)
app.register_blueprint(auth)
app.register_blueprint(user)
app.app_context().push() 
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', API_KEY_CONFIG)
# debug = DebugToolbarExtension(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///whichani')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)


######################################################
# Session handler
######################################################

@app.before_request
def add_user_to_g():
    """If logged in, add user to g."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


######################################################
# Home
######################################################

@app.route('/', methods=["GET"])
def home():
    """Render homepage based on login status."""

    return render_template('home.html')

######################################################
# Error page
######################################################

@app.errorhandler(404)
def page_not_found(e):
    """404 page."""

    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run()